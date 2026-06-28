"""Unit tests for document upload and storage service."""

import os
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import sys
sys.path.insert(0, ".")

from app.models.enums import DocumentType, VerificationStatus
from app.schemas.document import DocumentResponse, UploadDocumentResponse
from app.services.document_service import (
    ALLOWED_EXTENSIONS,
    ALLOWED_FILE_SIGNATURES,
    MAX_UPLOAD_SIZE_BYTES,
    DocumentService,
    DocumentServiceError,
    FileTooLargeError,
    InvalidFileTypeError,
    decrypt_file_content,
    encrypt_file_content,
    get_or_create_encryption_key,
    validate_file_extension,
    validate_file_size,
    validate_magic_bytes,
)


# ============================================================
# Test Data Helpers
# ============================================================

# Minimal valid file content with correct magic bytes
VALID_PDF_CONTENT = b"%PDF-1.4 fake pdf content for testing"
VALID_JPEG_CONTENT = b"\xff\xd8\xff\xe0" + b"\x00" * 100
VALID_PNG_CONTENT = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
VALID_TIFF_CONTENT_LE = b"II\x2a\x00" + b"\x00" * 100
VALID_TIFF_CONTENT_BE = b"MM\x00\x2a" + b"\x00" * 100
VALID_BMP_CONTENT = b"BM" + b"\x00" * 100


def _mock_db():
    """Create a mock async DB session."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


# ============================================================
# File Extension Validation Tests
# ============================================================


class TestValidateFileExtension:
    """Tests for validate_file_extension."""

    def test_valid_pdf_extension(self):
        """PDF extension should return application/pdf MIME type."""
        assert validate_file_extension("document.pdf") == "application/pdf"

    def test_valid_jpg_extension(self):
        """JPG extension should return image/jpeg MIME type."""
        assert validate_file_extension("photo.jpg") == "image/jpeg"

    def test_valid_jpeg_extension(self):
        """JPEG extension should return image/jpeg MIME type."""
        assert validate_file_extension("photo.jpeg") == "image/jpeg"

    def test_valid_png_extension(self):
        """PNG extension should return image/png MIME type."""
        assert validate_file_extension("image.png") == "image/png"

    def test_valid_tiff_extension(self):
        """TIFF extension should return image/tiff MIME type."""
        assert validate_file_extension("scan.tiff") == "image/tiff"

    def test_valid_tif_extension(self):
        """TIF extension should return image/tiff MIME type."""
        assert validate_file_extension("scan.tif") == "image/tiff"

    def test_valid_bmp_extension(self):
        """BMP extension should return image/bmp MIME type."""
        assert validate_file_extension("image.bmp") == "image/bmp"

    def test_case_insensitive_extension(self):
        """Extension validation should be case-insensitive."""
        assert validate_file_extension("Document.PDF") == "application/pdf"
        assert validate_file_extension("Photo.JPG") == "image/jpeg"
        assert validate_file_extension("image.PNG") == "image/png"

    def test_invalid_extension_raises(self):
        """Unsupported extensions should raise InvalidFileTypeError."""
        with pytest.raises(InvalidFileTypeError) as exc_info:
            validate_file_extension("script.exe")
        assert ".exe" in exc_info.value.message

    def test_no_extension_raises(self):
        """Files without an extension should raise InvalidFileTypeError."""
        with pytest.raises(InvalidFileTypeError):
            validate_file_extension("filename")

    def test_txt_extension_raises(self):
        """Text files should not be allowed."""
        with pytest.raises(InvalidFileTypeError):
            validate_file_extension("notes.txt")

    def test_docx_extension_raises(self):
        """Word documents should not be allowed."""
        with pytest.raises(InvalidFileTypeError):
            validate_file_extension("document.docx")


# ============================================================
# Magic Byte Validation Tests
# ============================================================


class TestValidateMagicBytes:
    """Tests for validate_magic_bytes."""

    def test_valid_pdf_magic_bytes(self):
        """PDF files starting with %PDF should pass validation."""
        assert validate_magic_bytes(VALID_PDF_CONTENT, "application/pdf") is True

    def test_valid_jpeg_magic_bytes(self):
        """JPEG files starting with 0xFFD8FF should pass validation."""
        assert validate_magic_bytes(VALID_JPEG_CONTENT, "image/jpeg") is True

    def test_valid_png_magic_bytes(self):
        """PNG files with correct header should pass validation."""
        assert validate_magic_bytes(VALID_PNG_CONTENT, "image/png") is True

    def test_valid_tiff_little_endian_magic_bytes(self):
        """TIFF files with little-endian header should pass validation."""
        assert validate_magic_bytes(VALID_TIFF_CONTENT_LE, "image/tiff") is True

    def test_valid_tiff_big_endian_magic_bytes(self):
        """TIFF files with big-endian header should pass validation."""
        assert validate_magic_bytes(VALID_TIFF_CONTENT_BE, "image/tiff") is True

    def test_valid_bmp_magic_bytes(self):
        """BMP files starting with BM should pass validation."""
        assert validate_magic_bytes(VALID_BMP_CONTENT, "image/bmp") is True

    def test_mismatched_magic_bytes_raises(self):
        """File content that doesn't match expected MIME type should raise error."""
        # PNG content claimed as PDF
        with pytest.raises(InvalidFileTypeError) as exc_info:
            validate_magic_bytes(VALID_PNG_CONTENT, "application/pdf")
        assert "does not match" in exc_info.value.message

    def test_random_bytes_raises(self):
        """Random bytes should not pass validation for any known type."""
        random_content = b"\x00\x01\x02\x03\x04\x05\x06\x07"
        with pytest.raises(InvalidFileTypeError):
            validate_magic_bytes(random_content, "application/pdf")

    def test_unsupported_mime_type_raises(self):
        """Unknown MIME types should raise InvalidFileTypeError."""
        with pytest.raises(InvalidFileTypeError) as exc_info:
            validate_magic_bytes(b"content", "application/unknown")
        assert "No magic byte signature" in exc_info.value.message


# ============================================================
# File Size Validation Tests
# ============================================================


class TestValidateFileSize:
    """Tests for validate_file_size."""

    def test_small_file_passes(self):
        """A 1KB file should pass size validation."""
        content = b"\x00" * 1024
        validate_file_size(content)  # Should not raise

    def test_exactly_at_limit_passes(self):
        """A file exactly at the size limit should pass."""
        content = b"\x00" * MAX_UPLOAD_SIZE_BYTES
        validate_file_size(content)  # Should not raise

    def test_over_limit_raises(self):
        """A file over the size limit should raise FileTooLargeError."""
        content = b"\x00" * (MAX_UPLOAD_SIZE_BYTES + 1)
        with pytest.raises(FileTooLargeError) as exc_info:
            validate_file_size(content)
        assert exc_info.value.status_code == 413

    def test_empty_file_passes(self):
        """An empty file should pass size validation (other checks handle empty)."""
        validate_file_size(b"")  # Should not raise


# ============================================================
# Encryption Tests
# ============================================================


class TestEncryption:
    """Tests for AES-256-GCM encryption and decryption."""

    def test_encrypt_decrypt_roundtrip(self):
        """Encrypting then decrypting should return original content."""
        key = os.urandom(32)
        content = b"This is a test document content for encryption"

        nonce, encrypted = encrypt_file_content(content, key)
        decrypted = decrypt_file_content(encrypted, key, nonce)

        assert decrypted == content

    def test_encrypt_produces_different_output(self):
        """Encrypted content should differ from original."""
        key = os.urandom(32)
        content = b"Original document content"

        nonce, encrypted = encrypt_file_content(content, key)

        assert encrypted != content

    def test_nonce_is_12_bytes(self):
        """GCM nonce should be exactly 12 bytes."""
        key = os.urandom(32)
        content = b"test"

        nonce, _ = encrypt_file_content(content, key)

        assert len(nonce) == 12

    def test_different_nonces_produce_different_ciphertext(self):
        """Two encryptions of the same content should produce different ciphertext."""
        key = os.urandom(32)
        content = b"Same content encrypted twice"

        nonce1, encrypted1 = encrypt_file_content(content, key)
        nonce2, encrypted2 = encrypt_file_content(content, key)

        # Nonces should be different (with overwhelming probability)
        assert nonce1 != nonce2
        # Ciphertext should be different
        assert encrypted1 != encrypted2

    def test_wrong_key_fails_decryption(self):
        """Decryption with wrong key should raise an error."""
        key1 = os.urandom(32)
        key2 = os.urandom(32)
        content = b"Secret content"

        nonce, encrypted = encrypt_file_content(content, key1)

        with pytest.raises(Exception):
            decrypt_file_content(encrypted, key2, nonce)

    def test_tampered_ciphertext_fails(self):
        """Modifying encrypted content should cause decryption to fail (GCM auth)."""
        key = os.urandom(32)
        content = b"Tamper test content"

        nonce, encrypted = encrypt_file_content(content, key)

        # Tamper with the ciphertext
        tampered = bytearray(encrypted)
        tampered[0] ^= 0xFF
        tampered = bytes(tampered)

        with pytest.raises(Exception):
            decrypt_file_content(tampered, key, nonce)

    def test_encrypt_empty_content(self):
        """Encrypting empty content should work."""
        key = os.urandom(32)
        content = b""

        nonce, encrypted = encrypt_file_content(content, key)
        decrypted = decrypt_file_content(encrypted, key, nonce)

        assert decrypted == content

    def test_encrypt_large_content(self):
        """Encrypting large content (1MB) should work."""
        key = os.urandom(32)
        content = os.urandom(1024 * 1024)  # 1MB

        nonce, encrypted = encrypt_file_content(content, key)
        decrypted = decrypt_file_content(encrypted, key, nonce)

        assert decrypted == content


# ============================================================
# Encryption Key Management Tests
# ============================================================


class TestGetOrCreateEncryptionKey:
    """Tests for get_or_create_encryption_key."""

    def test_returns_32_byte_key(self):
        """Key should always be 32 bytes (256 bits)."""
        key = get_or_create_encryption_key()
        assert len(key) == 32

    def test_consistent_key_without_env_var(self):
        """Without env var, key should be deterministic (derived from JWT secret)."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DOCUMENT_ENCRYPTION_KEY", None)
            key1 = get_or_create_encryption_key()
            key2 = get_or_create_encryption_key()
            assert key1 == key2

    def test_uses_env_var_when_set(self):
        """When DOCUMENT_ENCRYPTION_KEY is set, it should be used."""
        test_key = os.urandom(32).hex()
        with patch.dict(os.environ, {"DOCUMENT_ENCRYPTION_KEY": test_key}):
            key = get_or_create_encryption_key()
            assert key == bytes.fromhex(test_key)

    def test_invalid_env_key_length_raises(self):
        """An env key that's not 32 bytes should raise ValueError."""
        short_key = os.urandom(16).hex()  # Only 16 bytes
        with patch.dict(os.environ, {"DOCUMENT_ENCRYPTION_KEY": short_key}):
            with pytest.raises(ValueError, match="32 bytes"):
                get_or_create_encryption_key()


# ============================================================
# DocumentService.upload_document Tests
# ============================================================


class TestDocumentServiceUpload:
    """Tests for DocumentService.upload_document."""

    @pytest.mark.asyncio
    async def test_successful_pdf_upload(self, tmp_path):
        """A valid PDF file should be uploaded, encrypted, and stored."""
        db = _mock_db()
        service = DocumentService(db=db, upload_dir=str(tmp_path))
        submission_id = uuid.uuid4()

        result = await service.upload_document(
            file_content=VALID_PDF_CONTENT,
            filename="transcript.pdf",
            document_type=DocumentType.TRANSCRIPT,
            submission_id=submission_id,
        )

        assert isinstance(result, UploadDocumentResponse)
        assert result.submission_id == submission_id
        assert result.document_type == DocumentType.TRANSCRIPT
        assert result.original_filename == "transcript.pdf"
        assert result.file_size_bytes == len(VALID_PDF_CONTENT)
        assert result.mime_type == "application/pdf"
        assert result.status == VerificationStatus.PENDING
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_successful_jpeg_upload(self, tmp_path):
        """A valid JPEG file should be uploaded successfully."""
        db = _mock_db()
        service = DocumentService(db=db, upload_dir=str(tmp_path))

        result = await service.upload_document(
            file_content=VALID_JPEG_CONTENT,
            filename="id_photo.jpg",
            document_type=DocumentType.ID_DOCUMENT,
            submission_id=uuid.uuid4(),
        )

        assert result.mime_type == "image/jpeg"
        assert result.document_type == DocumentType.ID_DOCUMENT

    @pytest.mark.asyncio
    async def test_successful_png_upload(self, tmp_path):
        """A valid PNG file should be uploaded successfully."""
        db = _mock_db()
        service = DocumentService(db=db, upload_dir=str(tmp_path))

        result = await service.upload_document(
            file_content=VALID_PNG_CONTENT,
            filename="certificate.png",
            document_type=DocumentType.CERTIFICATE,
            submission_id=uuid.uuid4(),
        )

        assert result.mime_type == "image/png"

    @pytest.mark.asyncio
    async def test_file_too_large_raises(self, tmp_path):
        """Uploading a file larger than 10MB should raise FileTooLargeError."""
        db = _mock_db()
        service = DocumentService(db=db, upload_dir=str(tmp_path))

        # Create content slightly over the limit with valid PDF header
        large_content = b"%PDF" + b"\x00" * MAX_UPLOAD_SIZE_BYTES

        with pytest.raises(FileTooLargeError) as exc_info:
            await service.upload_document(
                file_content=large_content,
                filename="huge.pdf",
                document_type=DocumentType.REPORT,
                submission_id=uuid.uuid4(),
            )
        assert exc_info.value.status_code == 413

    @pytest.mark.asyncio
    async def test_invalid_extension_raises(self, tmp_path):
        """Uploading a file with unsupported extension should raise InvalidFileTypeError."""
        db = _mock_db()
        service = DocumentService(db=db, upload_dir=str(tmp_path))

        with pytest.raises(InvalidFileTypeError):
            await service.upload_document(
                file_content=b"some content",
                filename="malware.exe",
                document_type=DocumentType.CUSTOM,
                submission_id=uuid.uuid4(),
            )

    @pytest.mark.asyncio
    async def test_mismatched_magic_bytes_raises(self, tmp_path):
        """A file with valid extension but wrong magic bytes should raise InvalidFileTypeError."""
        db = _mock_db()
        service = DocumentService(db=db, upload_dir=str(tmp_path))

        # PNG content with .pdf extension
        with pytest.raises(InvalidFileTypeError) as exc_info:
            await service.upload_document(
                file_content=VALID_PNG_CONTENT,
                filename="fake.pdf",
                document_type=DocumentType.TRANSCRIPT,
                submission_id=uuid.uuid4(),
            )
        assert "does not match" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_encrypted_file_stored_on_disk(self, tmp_path):
        """The file stored on disk should be encrypted (different from original)."""
        db = _mock_db()
        service = DocumentService(db=db, upload_dir=str(tmp_path))

        result = await service.upload_document(
            file_content=VALID_PDF_CONTENT,
            filename="doc.pdf",
            document_type=DocumentType.REPORT,
            submission_id=uuid.uuid4(),
        )

        # Read stored file
        stored_path = os.path.join(str(tmp_path), str(result.id))
        with open(stored_path, "rb") as f:
            stored_data = f.read()

        # Stored data should not contain the original content in plaintext
        assert VALID_PDF_CONTENT not in stored_data
        # Stored data should be longer (nonce + ciphertext + auth tag)
        assert len(stored_data) > len(VALID_PDF_CONTENT)

    @pytest.mark.asyncio
    async def test_stored_file_can_be_decrypted(self, tmp_path):
        """The stored encrypted file should be decryptable back to original."""
        db = _mock_db()
        service = DocumentService(db=db, upload_dir=str(tmp_path))

        result = await service.upload_document(
            file_content=VALID_PDF_CONTENT,
            filename="doc.pdf",
            document_type=DocumentType.REPORT,
            submission_id=uuid.uuid4(),
        )

        # Read stored file
        stored_path = os.path.join(str(tmp_path), str(result.id))
        with open(stored_path, "rb") as f:
            stored_data = f.read()

        # Extract nonce (first 12 bytes) and encrypted data
        nonce = stored_data[:12]
        encrypted = stored_data[12:]

        # Decrypt and verify
        key = get_or_create_encryption_key()
        decrypted = decrypt_file_content(encrypted, key, nonce)
        assert decrypted == VALID_PDF_CONTENT

    @pytest.mark.asyncio
    async def test_all_document_types_supported(self, tmp_path):
        """All DocumentType enum values should be accepted."""
        db = _mock_db()
        service = DocumentService(db=db, upload_dir=str(tmp_path))

        for doc_type in DocumentType:
            result = await service.upload_document(
                file_content=VALID_PDF_CONTENT,
                filename="test.pdf",
                document_type=doc_type,
                submission_id=uuid.uuid4(),
            )
            assert result.document_type == doc_type

    @pytest.mark.asyncio
    async def test_document_gets_unique_id(self, tmp_path):
        """Each uploaded document should get a unique ID."""
        db = _mock_db()
        service = DocumentService(db=db, upload_dir=str(tmp_path))

        ids = set()
        for _ in range(5):
            result = await service.upload_document(
                file_content=VALID_PDF_CONTENT,
                filename="doc.pdf",
                document_type=DocumentType.REPORT,
                submission_id=uuid.uuid4(),
            )
            ids.add(result.id)

        assert len(ids) == 5

    @pytest.mark.asyncio
    async def test_upload_creates_directory_if_not_exists(self, tmp_path):
        """The service should create the upload directory if it doesn't exist."""
        upload_dir = str(tmp_path / "new_uploads" / "subdir")
        db = _mock_db()
        service = DocumentService(db=db, upload_dir=upload_dir)

        result = await service.upload_document(
            file_content=VALID_PDF_CONTENT,
            filename="doc.pdf",
            document_type=DocumentType.REPORT,
            submission_id=uuid.uuid4(),
        )

        assert os.path.exists(upload_dir)
        assert os.path.isfile(os.path.join(upload_dir, str(result.id)))


# ============================================================
# Schema Tests
# ============================================================


class TestDocumentSchemas:
    """Tests for document Pydantic schemas."""

    def test_document_response_from_attributes(self):
        """DocumentResponse should work with from_attributes mode."""
        doc_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        response = DocumentResponse(
            id=doc_id,
            submission_id=uuid.uuid4(),
            document_type=DocumentType.TRANSCRIPT,
            original_filename="test.pdf",
            storage_path="/uploads/test",
            file_size_bytes=1024,
            mime_type="application/pdf",
            encryption_algorithm="AES-256-GCM",
            encryption_key_id="default",
            uploaded_at=now,
        )
        assert response.id == doc_id
        assert response.encryption_algorithm == "AES-256-GCM"

    def test_upload_document_response_status_default(self):
        """UploadDocumentResponse should default status to PENDING."""
        response = UploadDocumentResponse(
            id=uuid.uuid4(),
            submission_id=uuid.uuid4(),
            document_type=DocumentType.CERTIFICATE,
            original_filename="cert.png",
            file_size_bytes=2048,
            mime_type="image/png",
            uploaded_at=datetime.now(timezone.utc),
        )
        assert response.status == VerificationStatus.PENDING


# ============================================================
# Error Class Tests
# ============================================================


class TestDocumentServiceErrors:
    """Tests for error class properties."""

    def test_file_too_large_error_status_code(self):
        """FileTooLargeError should have status 413."""
        err = FileTooLargeError(20_000_000)
        assert err.status_code == 413

    def test_invalid_file_type_error_status_code(self):
        """InvalidFileTypeError should have status 415."""
        err = InvalidFileTypeError()
        assert err.status_code == 415

    def test_document_not_found_error_status_code(self):
        """DocumentNotFoundError should have status 404."""
        from app.services.document_service import DocumentNotFoundError
        err = DocumentNotFoundError(uuid.uuid4())
        assert err.status_code == 404

    def test_base_error_default_status_code(self):
        """DocumentServiceError should default to 400."""
        err = DocumentServiceError("generic error")
        assert err.status_code == 400
