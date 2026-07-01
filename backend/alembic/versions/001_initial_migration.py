"""Initial migration - create all tables, indexes, and constraints.

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables, indexes, and constraints."""

    # --- Enum types ---
    userrole_enum = postgresql.ENUM(
        "super_admin", "org_admin", "recipient", name="userrole", create_type=False
    )
    programstatus_enum = postgresql.ENUM(
        "draft", "active", "paused", "completed", "archived",
        name="programstatus", create_type=False
    )
    requirementtype_enum = postgresql.ENUM(
        "academic_gwa", "enrollment_status", "document_submission",
        "milestone_completion", "attendance", "custom",
        name="requirementtype", create_type=False
    )
    applicationstatus_enum = postgresql.ENUM(
        "pending", "approved", "rejected", "withdrawn",
        name="applicationstatus", create_type=False
    )
    verificationstatus_enum = postgresql.ENUM(
        "pending", "processing", "auto_verified", "manual_review",
        "verified", "rejected", "processing_failed",
        name="verificationstatus", create_type=False
    )
    documenttype_enum = postgresql.ENUM(
        "grade_slip", "enrollment_form", "certificate", "transcript",
        "id_document", "report", "custom",
        name="documenttype", create_type=False
    )
    eligibilitystatus_enum = postgresql.ENUM(
        "eligible", "ineligible", "pending_verification", "partial",
        name="eligibilitystatus", create_type=False
    )
    notificationtype_enum = postgresql.ENUM(
        "application_received", "document_verified", "eligibility_determined",
        "funds_released", "manual_review_required", "program_update",
        name="notificationtype", create_type=False
    )

    # Create enum types
    userrole_enum.create(op.get_bind(), checkfirst=True)
    programstatus_enum.create(op.get_bind(), checkfirst=True)
    requirementtype_enum.create(op.get_bind(), checkfirst=True)
    applicationstatus_enum.create(op.get_bind(), checkfirst=True)
    verificationstatus_enum.create(op.get_bind(), checkfirst=True)
    documenttype_enum.create(op.get_bind(), checkfirst=True)
    eligibilitystatus_enum.create(op.get_bind(), checkfirst=True)
    notificationtype_enum.create(op.get_bind(), checkfirst=True)

    # --- Table: organizations ---
    op.create_table(
        "organizations",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(512), nullable=True),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # --- Table: users ---
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", userrole_enum, nullable=False),
        sa.Column("organization_id", sa.UUID(), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    # --- Table: programs ---
    op.create_table(
        "programs",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("organization_id", sa.UUID(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", programstatus_enum, server_default="draft", nullable=False),
        sa.Column("funding_amount_per_recipient", sa.Numeric(12, 2), nullable=False),
        sa.Column("max_recipients", sa.Integer(), nullable=False),
        sa.Column("current_recipients", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("total_funded", sa.Numeric(14, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("end_date", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # --- Table: program_requirements ---
    op.create_table(
        "program_requirements",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("program_id", sa.UUID(), sa.ForeignKey("programs.id"), nullable=False),
        sa.Column("requirement_type", requirementtype_enum, nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("condition_operator", sa.String(20), nullable=False),
        sa.Column("condition_value", sa.String(255), nullable=False),
        sa.Column("is_mandatory", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("verification_frequency", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # --- Table: applications ---
    op.create_table(
        "applications",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("recipient_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("program_id", sa.UUID(), sa.ForeignKey("programs.id"), nullable=False),
        sa.Column("status", applicationstatus_enum, server_default="pending", nullable=False),
        sa.Column("submitted_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_by", sa.UUID(), sa.ForeignKey("users.id"), nullable=True),
    )

    # --- Table: compliance_submissions ---
    op.create_table(
        "compliance_submissions",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("recipient_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("program_id", sa.UUID(), sa.ForeignKey("programs.id"), nullable=False),
        sa.Column(
            "requirement_id", sa.UUID(),
            sa.ForeignKey("program_requirements.id"), nullable=False
        ),
        sa.Column("status", verificationstatus_enum, server_default="pending", nullable=False),
        sa.Column("submitted_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("verified_by", sa.UUID(), sa.ForeignKey("users.id"), nullable=True),
    )

    # --- Table: uploaded_documents ---
    op.create_table(
        "uploaded_documents",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "submission_id", sa.UUID(),
            sa.ForeignKey("compliance_submissions.id"), nullable=False
        ),
        sa.Column("document_type", documenttype_enum, nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("storage_path", sa.String(512), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column(
            "encryption_algorithm", sa.String(50),
            server_default="AES-256-GCM", nullable=False
        ),
        sa.Column("encryption_key_id", sa.String(255), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # --- Table: ocr_results ---
    op.create_table(
        "ocr_results",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "submission_id", sa.UUID(),
            sa.ForeignKey("compliance_submissions.id"), nullable=False
        ),
        sa.Column(
            "document_id", sa.UUID(),
            sa.ForeignKey("uploaded_documents.id"), nullable=False
        ),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("structured_data", postgresql.JSON(), nullable=True),
        sa.Column("confidence_score", sa.Numeric(5, 4), nullable=False),
        sa.Column("extraction_metadata", postgresql.JSON(), nullable=True),
        sa.Column("processing_time_ms", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # --- Table: eligibility_evaluations ---
    op.create_table(
        "eligibility_evaluations",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "submission_id", sa.UUID(),
            sa.ForeignKey("compliance_submissions.id"), nullable=False
        ),
        sa.Column("recipient_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("program_id", sa.UUID(), sa.ForeignKey("programs.id"), nullable=False),
        sa.Column("overall_status", eligibilitystatus_enum, nullable=False),
        sa.Column("rule_results", postgresql.JSON(), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("next_evaluation_due", sa.DateTime(), nullable=True),
    )

    # --- Table: stellar_wallets ---
    op.create_table(
        "stellar_wallets",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("public_key", sa.String(56), nullable=False),
        sa.Column("encrypted_private_key", sa.String(512), nullable=False),
        sa.Column("encryption_key_id", sa.String(255), nullable=False),
        sa.Column("network", sa.String(20), server_default="testnet", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_stellar_wallets_user_id"),
        sa.UniqueConstraint("public_key", name="uq_stellar_wallets_public_key"),
    )

    # --- Table: funding_pools ---
    op.create_table(
        "funding_pools",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("program_id", sa.UUID(), sa.ForeignKey("programs.id"), nullable=False),
        sa.Column("public_key", sa.String(56), nullable=False),
        sa.Column("encrypted_private_key", sa.String(512), nullable=False),
        sa.Column("balance", sa.Numeric(14, 7), server_default=sa.text("0"), nullable=False),
        sa.Column("contract_id", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("network", sa.String(20), server_default="testnet", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("program_id", name="uq_funding_pools_program_id"),
        sa.UniqueConstraint("public_key", name="uq_funding_pools_public_key"),
    )

    # --- Table: transactions ---
    op.create_table(
        "transactions",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("program_id", sa.UUID(), sa.ForeignKey("programs.id"), nullable=False),
        sa.Column("recipient_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("stellar_tx_hash", sa.String(64), nullable=False),
        sa.Column("from_address", sa.String(56), nullable=False),
        sa.Column("to_address", sa.String(56), nullable=False),
        sa.Column("amount", sa.Numeric(14, 7), nullable=False),
        sa.Column("asset_code", sa.String(12), server_default="XLM", nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("memo", sa.String(28), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("stellar_tx_hash", name="uq_transactions_stellar_tx_hash"),
    )

    # --- Table: notifications ---
    op.create_table(
        "notifications",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("notification_type", notificationtype_enum, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.String(1000), nullable=True),
        sa.Column("payload", postgresql.JSON(), nullable=True),
        sa.Column("is_read", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("read_at", sa.DateTime(), nullable=True),
    )

    # --- Table: audit_logs ---
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.String(36), nullable=False),
        sa.Column("details", postgresql.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # --- Indexes ---

    # users.email (for fast login lookups)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # programs.organization_id + status (for org-scoped program listing with status filter)
    op.create_index(
        "ix_programs_organization_id_status", "programs", ["organization_id", "status"]
    )

    # transactions.program_id + created_at (for program transaction history queries)
    op.create_index(
        "ix_transactions_program_id_created_at", "transactions", ["program_id", "created_at"]
    )

    # compliance_submissions.recipient_id + program_id (for recipient compliance lookups)
    op.create_index(
        "ix_compliance_submissions_recipient_id_program_id",
        "compliance_submissions",
        ["recipient_id", "program_id"],
    )

    # Additional useful indexes
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_resource_type", "audit_logs", ["resource_type"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("ix_applications_recipient_id", "applications", ["recipient_id"])
    op.create_index("ix_applications_program_id", "applications", ["program_id"])


def downgrade() -> None:
    """Drop all tables and enum types."""

    # Drop indexes
    op.drop_index("ix_applications_program_id", table_name="applications")
    op.drop_index("ix_applications_recipient_id", table_name="applications")
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_resource_type", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_index(
        "ix_compliance_submissions_recipient_id_program_id",
        table_name="compliance_submissions",
    )
    op.drop_index("ix_transactions_program_id_created_at", table_name="transactions")
    op.drop_index("ix_programs_organization_id_status", table_name="programs")
    op.drop_index("ix_users_email", table_name="users")

    # Drop tables in reverse dependency order
    op.drop_table("audit_logs")
    op.drop_table("notifications")
    op.drop_table("transactions")
    op.drop_table("funding_pools")
    op.drop_table("stellar_wallets")
    op.drop_table("eligibility_evaluations")
    op.drop_table("ocr_results")
    op.drop_table("uploaded_documents")
    op.drop_table("compliance_submissions")
    op.drop_table("applications")
    op.drop_table("program_requirements")
    op.drop_table("programs")
    op.drop_table("users")
    op.drop_table("organizations")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS notificationtype")
    op.execute("DROP TYPE IF EXISTS eligibilitystatus")
    op.execute("DROP TYPE IF EXISTS documenttype")
    op.execute("DROP TYPE IF EXISTS verificationstatus")
    op.execute("DROP TYPE IF EXISTS applicationstatus")
    op.execute("DROP TYPE IF EXISTS requirementtype")
    op.execute("DROP TYPE IF EXISTS programstatus")
    op.execute("DROP TYPE IF EXISTS userrole")
