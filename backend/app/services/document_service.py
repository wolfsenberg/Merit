"""Document upload and storage service with file validation and encryption."""

import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.enums import DocumentType, VerificationStatus
from app.models.uploaded_document import UploadedDocument
from app.schemas.document import UploadDocumentResponse

settings = get_settings()

# Maximum upload size in bytes (10 MB)
MAX_UPLOAD_SIZE_BYTES = settings.max_upload_size_mb * 1024 * 1024

# Allowed MIME types with their magic byte signatures
# Each entry maps a MIME type to a list of possible magic byte prefixes
ALLOWED_FILE_SIGNATURES: dict[str, list[bytes]] = {
    "application/pdf": [b"%PDF"],
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/tiff": [b"II\x2a\x00", b"MM\x00\x2a"],
    "image/bmp": [b"BM"],
}

# Map file extensions to expected MIME types
ALLOWED_EXTENSIONS: dict[str, str] = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
    ".bmp": "image/bmp",
}


class DocumentServiceError(Exception):
    """Base exception for document service errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class FileTooLargeError(DocumentServiceError):
    """Raised when uploaded file exceeds size limit."""

    def __init__(self, file_size: int):
        max_mb = settings.max_upload_size_mb
        super().__init__(
            f"File size ({file_size} bytes) exceeds maximum allowed size ({max_mb}MB)",
            status_code=413,
        )


class InvalidFileTypeError(DocumentServiceError):
    """Raised when file type is not allowed or magic bytes don't match extension."""

    def __init__(self, message: str = "Invalid or unsupported file type"):
        super().__init__(message, status_code=415)


class DocumentNotFoundError(DocumentServiceError):
    """Raised when a document is not found."""

    def __init__(self, document_id: uuid.UUID):
        super().__init__(f"Document {document_id} not found", status_code=404)


def validate_file_extension(filename: str) -> str:
    """Validate and return the MIME type based on file extension.

    Args:
        filename: The original filename with extension.

    Returns:
        The expected MIME type for the extension.

    Raises:
        InvalidFileTypeError: If the extension is not allowed.
    """
    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        raise InvalidFileTypeError(
            f"File extension '{ext}' is not allowed. "
            f"Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS.keys()))}"
        )
    return ALLOWED_EXTENSIONS[ext]


def validate_magic_bytes(file_content: bytes, expected_mime_type: str) -> bool:
    """Validate file content against magic byte signatures.

    Args:
        file_content: The raw file bytes.
        expected_mime_type: The MIME type expected based on the file extension.

    Returns:
        True if magic bytes match the expected MIME type.

    Raises:
        InvalidFileTypeError: If magic bytes don't match expected type.
    """
    if expected_mime_type not in ALLOWED_FILE_SIGNATURES:
        raise InvalidFileTypeError(
            f"No magic byte signature defined for MIME type '{expected_mime_type}'"
        )

    signatures = ALLOWED_FILE_SIGNATURES[expected_mime_type]
    for sig in signatures:
        if file_content[: len(sig)] == sig:
            return True

    raise InvalidFileTypeError(
        "File content does not match the expected file type based on magic bytes. "
        "The file may be corrupted or have an incorrect extension."
    )


def validate_file_size(file_content: bytes) -> None:
    """Validate that file content does not exceed maximum size.

    Args:
        file_content: The raw file bytes.

    Raises:
        FileTooLargeError: If the file exceeds MAX_UPLOAD_SIZE_BYTES.
    """
    if len(file_content) > MAX_UPLOAD_SIZE_BYTES:
        raise FileTooLargeError(len(file_content))


def encrypt_file_content(file_content: bytes, encryption_key: bytes) -> tuple[bytes, bytes]:
    """Encrypt file content using AES-256-GCM.

    Args:
        file_content: The raw file bytes to encrypt.
        encryption_key: A 32-byte (256-bit) encryption key.

    Returns:
        A tuple of (nonce, encrypted_data). The nonce is needed for decryption.
    """
    aesgcm = AESGCM(encryption_key)
    nonce = os.urandom(12)  # 96-bit nonce for GCM
    encrypted_data = aesgcm.encrypt(nonce, file_content, None)
    return nonce, encrypted_data


def decrypt_file_content(
    encrypted_data: bytes, encryption_key: bytes, nonce: bytes
) -> bytes:
    """Decrypt file content using AES-256-GCM.

    Args:
        encrypted_data: The encrypted file bytes.
        encryption_key: The 32-byte (256-bit) encryption key used for encryption.
        nonce: The 12-byte nonce used during encryption.

    Returns:
        The decrypted file content.
    """
    aesgcm = AESGCM(encryption_key)
    return aesgcm.decrypt(nonce, encrypted_data, None)


def get_or_create_encryption_key() -> bytes:
    """Get or generate an encryption key for document storage.

    In production, this would retrieve the key from a secure key management
    service (e.g., AWS KMS, HashiCorp Vault). For now, it generates a
    deterministic key from the JWT secret or uses environment variable.

    Returns:
        A 32-byte AES-256 encryption key.
    """
    # Check for explicit encryption key in environment
    env_key = os.environ.get("DOCUMENT_ENCRYPTION_KEY")
    if env_key:
        # Expect hex-encoded 32-byte key
        key_bytes = bytes.fromhex(env_key)
        if len(key_bytes) != 32:
            raise ValueError("DOCUMENT_ENCRYPTION_KEY must be exactly 32 bytes (64 hex chars)")
        return key_bytes

    # Fallback: derive from JWT secret (development only)
    import hashlib

    return hashlib.sha256(settings.jwt_secret_key.encode()).digest()


class DocumentService:
    """Service handling document upload, validation, encryption, and storage."""

    def __init__(self, db: AsyncSession, upload_dir: Optional[str] = None):
        self.db = db
        self.upload_dir = upload_dir or settings.upload_dir

    async def upload_document(
        self,
        file_content: bytes,
        filename: str,
        document_type: DocumentType,
        submission_id: uuid.UUID,
    ) -> UploadDocumentResponse:
        """Upload, validate, encrypt, and store a document.

        Args:
            file_content: The raw file bytes.
            filename: The original filename (including extension).
            document_type: The type of document being uploaded.
            submission_id: The compliance submission this document belongs to.

        Returns:
            UploadDocumentResponse with the created document metadata.

        Raises:
            FileTooLargeError: If file exceeds max size.
            InvalidFileTypeError: If file type is invalid or magic bytes don't match.
        """
        # Step 1: Validate file size
        validate_file_size(file_content)

        # Step 2: Validate file extension
        expected_mime_type = validate_file_extension(filename)

        # Step 3: Validate magic bytes match extension
        validate_magic_bytes(file_content, expected_mime_type)

        # Step 4: Encrypt the file content
        encryption_key = get_or_create_encryption_key()
        nonce, encrypted_data = encrypt_file_content(file_content, encryption_key)

        # Step 5: Store encrypted file to filesystem
        document_id = uuid.uuid4()
        storage_path = await self._store_encrypted_file(
            document_id, nonce, encrypted_data
        )

        # Step 6: Create database record
        document = UploadedDocument(
            id=document_id,
            submission_id=submission_id,
            document_type=document_type,
            original_filename=filename,
            storage_path=storage_path,
            file_size_bytes=len(file_content),
            mime_type=expected_mime_type,
            encryption_algorithm="AES-256-GCM",
            encryption_key_id="default",
            uploaded_at=datetime.now(timezone.utc),
        )

        self.db.add(document)
        await self.db.flush()

        return UploadDocumentResponse(
            id=document.id,
            submission_id=document.submission_id,
            document_type=document.document_type,
            original_filename=document.original_filename,
            file_size_bytes=document.file_size_bytes,
            mime_type=document.mime_type,
            status=VerificationStatus.PENDING,
            uploaded_at=document.uploaded_at,
        )

    async def _store_encrypted_file(
        self, document_id: uuid.UUID, nonce: bytes, encrypted_data: bytes
    ) -> str:
        """Store encrypted file content to the filesystem.

        The file is stored as: {upload_dir}/{document_id}
        The first 12 bytes of the stored file are the nonce, followed by encrypted data.

        Args:
            document_id: Unique ID for the document.
            nonce: The 12-byte GCM nonce.
            encrypted_data: The AES-256-GCM encrypted file content.

        Returns:
            The relative storage path for the file.
        """
        # Ensure upload directory exists
        os.makedirs(self.upload_dir, exist_ok=True)

        storage_path = os.path.join(self.upload_dir, str(document_id))

        # Write nonce + encrypted data
        with open(storage_path, "wb") as f:
            f.write(nonce)
            f.write(encrypted_data)

        return storage_path
