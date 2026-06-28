# Implementation Plan: Merit Platform

## Overview

Implementation of the Merit AI-assisted conditional funding platform. The backend is built with FastAPI (Python), the frontend with Next.js 15 (TypeScript), smart contracts with Soroban (Rust), and infrastructure with Docker Compose. Tasks are ordered to build foundational layers first, then service layers, then integration and frontend.

## Tasks

- [x] 1. Set up project structure and infrastructure
  - [x] 1.1 Initialize backend project with FastAPI and dependencies
    - Create `backend/` directory with `pyproject.toml` or `requirements.txt`
    - Configure FastAPI app entry point (`main.py`) with CORS, middleware slots, and API versioning prefix `/api/v1`
    - Set up SQLAlchemy async engine configuration with connection pooling (pool_size=20, max_overflow=10)
    - Configure Alembic for database migrations
    - Set up Redis connection for caching and session storage
    - Set up Celery/ARQ task queue configuration
    - _Requirements: 14.6, 14.7, 15.1_

  - [x] 1.2 Initialize frontend project with Next.js 15
    - Create `frontend/` directory with Next.js 15 App Router, TypeScript, Tailwind CSS
    - Install and configure shadcn/ui component library
    - Configure TanStack Query provider and Zustand store
    - Set up Zod schema validation utilities
    - Implement gold and white color scheme in Tailwind config
    - Set up mobile-first responsive breakpoints
    - _Requirements: 13.1, 13.2, 13.4, 13.5_

  - [x] 1.3 Initialize Soroban smart contract project
    - Create `contracts/` directory with Cargo workspace
    - Set up `soroban-sdk` dependency and contract skeleton
    - Configure testnet deployment scripts
    - _Requirements: 9.1_

  - [x] 1.4 Create Docker Compose configuration
    - Define services: nginx, next, fastapi, celery-worker, postgres, redis
    - Configure Nginx reverse proxy with TLS termination and routing (`/` → Next.js, `/api` → FastAPI)
    - Set all containers to run as non-root users
    - Configure environment variable management for secrets
    - _Requirements: 15.1, 15.2, 15.4, 15.5_

- [x] 2. Implement database models and migrations
  - [x] 2.1 Create SQLAlchemy data models
    - Implement User model with role enum, password_hash, organization relationship
    - Implement Organization model with members and programs relationships
    - Implement Program model with status enum, requirements, funding_pool relationships
    - Implement ProgramRequirement model with type enum, condition fields, mandatory flag
    - Implement Application model linking recipients to programs
    - Implement ComplianceSubmission model with documents and OCR results relationships
    - Implement UploadedDocument model with encryption metadata
    - Implement OCRResult model with structured_data JSON field
    - Implement EligibilityEvaluation model with rule_results JSON
    - Implement StellarWallet model with encrypted private key storage
    - Implement FundingPool model with balance and contract_id
    - Implement Transaction model with stellar_tx_hash unique constraint
    - Implement Notification model with type enum and read status
    - Implement AuditLog model (append-only)
    - _Requirements: 1.1, 3.1, 5.1, 7.8, 8.1, 11.1_

  - [x] 2.2 Generate and run Alembic migrations
    - Create initial migration with all tables, indexes, and constraints
    - Add indexes on: users.email, programs.organization_id+status, transactions.program_id+created_at, compliance_submissions.recipient_id+program_id
    - _Requirements: 14.3, 14.6_

- [ ] 3. Implement Authentication Service
  - [x] 3.1 Implement user registration and login
    - Create `RegisterRequest` and `LoginRequest` Pydantic schemas with validation (password min 8 chars)
    - Implement bcrypt password hashing with cost factor 12
    - Implement JWT access token generation (15-min expiry) and refresh token (7-day expiry)
    - Implement token refresh with rotation
    - Validate organization_id required for org_admin role
    - Implement duplicate email rejection
    - Implement account lockout after 5 failed attempts (30-min cooldown)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8_

  - [x] 3.2 Implement RBAC middleware
    - Create dependency injection middleware that validates JWT on every protected endpoint
    - Implement role-based permission checks (Super Admin unrestricted, Org Admin org-scoped, Recipient limited)
    - Return 401 for expired/invalid tokens, 403 for insufficient role
    - Enforce organization scoping for Org Admin endpoints
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [x] 3.3 Write property tests for authentication
    - **Property P8: Role-Based Access Control** - For all role/endpoint combinations, access is correctly granted or denied
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**

  - [x] 3.3 Create auth API routes
    - POST `/api/v1/auth/register` - User registration
    - POST `/api/v1/auth/login` - User login
    - POST `/api/v1/auth/refresh` - Token refresh
    - POST `/api/v1/auth/reset-password` - Password reset request
    - Implement rate limiting: 20 req/min unauthenticated, 100 req/min authenticated
    - _Requirements: 1.1, 1.2, 1.3, 14.1, 14.5_

- [ ] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement Program Service
  - [x] 5.1 Implement program CRUD operations
    - Create program in DRAFT status with validation (funding_amount > 0, max_recipients >= 1, end_date > start_date)
    - Implement program status lifecycle: DRAFT → ACTIVE → PAUSED ↔ ACTIVE → COMPLETED → ARCHIVED
    - Implement activate, pause, resume status transitions with guard checks
    - Implement organization-scoped listing with cursor-based pagination
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 14.8_

  - [x6] 5.2 Implement requirement management
    - Add/remove requirements with type, condition_operator, condition_value, is_mandatory, verification_frequency
    - Support all requirement types: academic_gwa, enrollment_status, document_submission, milestone_completion, attendance, custom
    - _Requirements: 3.9, 3.10_

  - [x] 5.3 Implement recipient application flow
    - Create application record for recipient → ACTIVE program
    - Reject applications to non-ACTIVE programs
    - Reject applications when max_recipients reached
    - Record application timestamp and initial status
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [x] 5.4 Write property test for program status lifecycle
    - **Property P10: Program Status Lifecycle** - Status transitions follow valid lifecycle graph; no illegal transitions
    - **Validates: Requirements 3.2, 3.3, 3.4, 3.5**

  - [x] 5.5 Create program API routes
    - GET/POST `/api/v1/programs` - List and create programs
    - GET/PUT `/api/v1/programs/{id}` - Get and update program
    - POST `/api/v1/programs/{id}/requirements` - Add requirement
    - POST `/api/v1/programs/{id}/activate` - Activate program
    - POST `/api/v1/programs/{id}/pause` - Pause program
    - POST `/api/v1/applications` - Submit application
    - GET `/api/v1/applications` - List applications
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.1_

- [ ] 6. Implement Verification Service and OCR Pipeline
  - [x] 6.1 Implement document upload and storage
    - Validate file type via magic byte checking and extension (max 10MB)
    - Encrypt documents at rest using AES-256
    - Create document record with PENDING status
    - Support document types: grade_slip, enrollment_form, certificate, transcript, id_document, report, custom
    - _Requirements: 5.1, 5.8, 5.9, 14.4_

  - [x] 6.2 Implement OCR processing pipeline
    - Integrate EasyOCR/PaddleOCR for text extraction
    - Implement structured data extraction with field identification (pattern matching per document type)
    - Implement confidence scoring based on field completeness and OCR engine confidence
    - Process documents asynchronously via Celery/ARQ task queue
    - _Requirements: 5.2, 5.3, 5.10_

  - [x] 6.3 Implement verification decision logic
    - Auto-verify when confidence >= program threshold
    - Flag for manual review when confidence < threshold, notify Org Admin
    - Set PROCESSING_FAILED on file corruption/unsupported format, notify Recipient
    - Implement manual verify/reject endpoint for Org Admin
    - _Requirements: 5.4, 5.5, 5.6, 5.7_

  - [x] 6.4 Write property tests for confidence scoring and verification
    - **Property P4: Document Processing Determinism** - Same document content always yields identical structured_data and confidence_score
    - **Validates: Requirements 5.10**

  - [x] 6.5 Create verification API routes
    - POST `/api/v1/documents/upload` - Upload document
    - GET `/api/v1/documents/{id}/ocr` - Get OCR result
    - POST `/api/v1/documents/{id}/verify` - Manual verification (Org Admin)
    - _Requirements: 5.1, 5.6_

- [ ] 7. Implement Compliance Engine
  - [x] 7.1 Implement condition evaluation function
    - Support operators: lte, gte, eq, neq, lt, gt, contains, exists, not_exists
    - Implement numeric comparisons with parse-error fail-safe (return False)
    - Implement case-insensitive string comparisons for eq and contains
    - Implement exists/not_exists checks for None and empty/whitespace values
    - _Requirements: 6.6, 6.7, 6.8, 6.9, 6.10_

  - [x] 7.2 Write property tests for condition evaluation
    - **Property P5: Condition Evaluation Consistency** - evaluate_condition is deterministic; numeric operators satisfy mathematical relationships; None returns False except for not_exists
    - **Validates: Requirements 6.6, 6.7, 6.8, 6.9, 6.10**

  - [x] 7.3 Implement eligibility evaluation algorithm
    - Evaluate all program requirements against recipient's verified submissions
    - Determine ELIGIBLE when all mandatory pass, INELIGIBLE when any mandatory fails, PENDING_VERIFICATION when submissions missing, PARTIAL when optional pass but mandatory fail
    - Record evaluation with timestamp and schedule next evaluation
    - Implement batch evaluation for all recipients in a program
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.11, 6.12_

  - [x] 7.4 Write property tests for eligibility evaluation
    - **Property P3: Verification Completeness** - ELIGIBLE status implies all mandatory requirements have passing rule_results
    - **Validates: Requirements 6.2, 6.3**

  - [x] 7.5 Create compliance API routes
    - GET `/api/v1/compliance/{recipient_id}/{program_id}` - Get compliance status
    - POST `/api/v1/compliance/evaluate` - Trigger evaluation
    - _Requirements: 6.1, 6.12_

- [ ] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Implement Funding Service and Stellar Integration
  - [x] 9.1 Implement Stellar wallet management
    - Generate Stellar keypair for recipients
    - Enforce wallet uniqueness per user (at most one wallet)
    - Store private keys in encrypted vault (never in code/config)
    - Create funding pool accounts on Stellar network
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [x] 9.2 Write property test for wallet uniqueness
    - **Property P9: Wallet Uniqueness** - Each user has at most one StellarWallet; wallet public keys are globally unique
    - **Validates: Requirements 8.2**

  - [x] 9.3 Implement fund disbursement flow
    - Verify compliance evaluation is ELIGIBLE
    - Check pool balance >= requested amount, reject if insufficient
    - Reject disbursement if pool is paused
    - Invoke Soroban contract for on-chain verification
    - Execute Stellar payment transfer
    - Record transaction with stellar_tx_hash
    - Decrement pool balance atomically, increment program total_funded
    - Implement database advisory locks to prevent double-spend on concurrent requests
    - Implement retry with exponential backoff (max 5 attempts over 15 min) for Stellar failures
    - Create pending transactions for unreachable network, retry via background job
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 16.1, 16.2, 16.3_

  - [x] 9.4 Write property tests for funding integrity
    - **Property P1: Funding Integrity** - No transaction overdraws a funding pool; sum of all transactions equals program total_disbursed
    - **Property P2: Eligibility Prerequisite** - Funds are never released without a valid ELIGIBLE compliance evaluation
    - **Validates: Requirements 7.1, 7.2, 7.4**

  - [x] 9.5 Create funding API routes
    - GET `/api/v1/funding/wallet` - Get wallet info
    - POST `/api/v1/funding/wallet` - Create wallet
    - POST `/api/v1/programs/{id}/fund` - Fund program pool
    - POST `/api/v1/funding/disburse` - Disburse funds
    - GET `/api/v1/transactions` - Transaction history
    - _Requirements: 7.7, 7.8, 8.1_

- [ ] 10. Implement Soroban Smart Contract
  - [x] 10.1 Implement MeritFundingContract in Rust
    - Implement `create_program` - store program state with org_id, funding_amount, max_recipients, Active status; require org authorization
    - Implement `register_recipient` - store recipient state, increment current_recipients, reject when max reached
    - Implement `submit_verification` - update eligibility status and verification timestamp
    - Implement `release_funds` - transfer from pool to recipient wallet, reject non-eligible, reject paused programs; update total_disbursed
    - Implement `pause_funding` / `resume_funding` - require org authorization, block disbursements while paused
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8_

  - [x] 10.2 Write unit tests for smart contract
    - Test program creation with valid/invalid parameters
    - Test recipient registration up to and beyond max_recipients
    - Test fund release with eligible/ineligible recipients
    - Test pause/resume lifecycle and authorization checks
    - **Property P6: Smart Contract State Consistency** - total_disbursed equals sum of all release_funds calls; current_recipients equals count of registered recipients
    - **Validates: Requirements 9.1, 9.2, 9.3, 9.5, 9.6, 9.7, 9.8**

- [ ] 11. Implement Notification and Audit Services
  - [x] 11.1 Implement Notification Service
    - Send notifications for: document verified, eligibility determined, funds released, manual review required
    - Implement get notifications with unread/read filter
    - Implement mark as read
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

  - [x] 11.2 Implement Audit Logging
    - Create audit log entries for all state-changing operations (user_id, action, resource_type, resource_id, details, IP, timestamp)
    - Record compliance evaluations, disbursements, program status changes
    - Enforce append-only (no modification or deletion)
    - Support filtering by user, action, resource type, time range
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

  - [x] 11.3 Write property test for audit trail completeness
    - **Property P7: Audit Trail Completeness** - Every state-changing operation produces an audit log entry within 1 second
    - **Validates: Requirements 11.1, 11.2, 11.3, 11.4**

  - [x] 11.4 Create notification and audit API routes
    - GET `/api/v1/notifications` - Get user notifications
    - PUT `/api/v1/notifications/{id}/read` - Mark as read
    - GET `/api/v1/admin/audit-logs` - Query audit logs (Super Admin)
    - _Requirements: 10.5, 10.6, 11.6_

- [ ] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Implement Frontend - Authentication and Layout
  - [x] 13.1 Implement shared layout and navigation
    - Create root layout with gold/white color scheme, responsive sidebar navigation
    - Implement mobile-first responsive design with hamburger menu for mobile
    - Set up server-side rendering for initial page loads
    - Implement code splitting per route
    - _Requirements: 13.1, 13.2, 13.3, 13.7_

  - [x] 13.2 Implement authentication pages
    - Build registration form with Zod validation (email, password, full name, role selection)
    - Build login form with error handling
    - Implement JWT token storage and auto-refresh interceptor
    - Implement protected route wrapper with role-based redirects
    - _Requirements: 1.1, 1.2, 1.4, 13.5_

  - [x] 13.3 Implement API client layer
    - Create typed API client with TanStack Query integration
    - Implement stale-while-revalidate caching strategy
    - Implement error handling and 401 auto-refresh logic
    - _Requirements: 13.4_

- [ ] 14. Implement Frontend - Organization Admin Dashboard
  - [x] 14.1 Implement program management pages
    - Build program creation form with multi-step wizard (details → requirements → review)
    - Build program listing with status filters and pagination
    - Build program detail page with status controls (activate, pause, resume)
    - Build requirement configuration UI
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.9, 3.10, 13.5_

  - [x] 14.2 Implement verification management pages
    - Build document review queue for flagged documents
    - Build manual verification interface with approve/reject and notes
    - Display OCR extracted data and confidence score
    - _Requirements: 5.5, 5.6_

  - [x] 14.3 Implement program analytics dashboard
    - Display current recipients, total funded, compliance rates, disbursement history
    - Build charts for funding over time
    - _Requirements: 12.4_

- [ ] 15. Implement Frontend - Recipient Dashboard
  - [x] 15.1 Implement application flow
    - Build program discovery/listing page for active programs
    - Build application submission form
    - Build application status tracking page
    - _Requirements: 4.1, 4.2_

  - [x] 15.2 Implement document upload interface
    - Build document upload with drag-and-drop, file type/size validation
    - Implement client-side image compression before upload
    - Display upload progress and processing status
    - Show OCR results and verification status
    - _Requirements: 5.1, 13.6_

  - [x] 15.3 Implement wallet and funding pages
    - Build wallet creation flow
    - Display wallet balance and transaction history
    - Show disbursement notifications with transaction details
    - _Requirements: 8.1, 7.7_

- [ ] 16. Implement Frontend - Super Admin Dashboard
  - [x] 16.1 Implement admin analytics and user management
    - Build platform-wide analytics dashboard (total users, orgs, programs, transactions)
    - Build user management interface with role and status display
    - Build organization listing with verification status and program counts
    - Build audit log viewer with filtering by user, action, resource type, time range
    - _Requirements: 12.1, 12.2, 12.3, 11.6_

- [ ] 17. Implement API Security and Rate Limiting
  - [x] 17.1 Implement rate limiting and security middleware
    - Configure rate limiting: 100 req/min authenticated, 20 req/min unauthenticated via Redis
    - Return 429 Too Many Requests when limits exceeded
    - Validate file uploads with magic byte checking
    - Ensure all queries use parameterized ORM (SQLAlchemy) for SQL injection prevention
    - _Requirements: 14.1, 14.3, 14.4, 14.5_

- [ ] 18. Implement CI/CD Pipeline
  - [x] 18.1 Create GitHub Actions workflow
    - Configure pipeline stages: lint, test, build, integration test, security scan, deploy
    - Run dependency vulnerability scanning (Snyk/Dependabot)
    - Deploy to EC2 on push to main branch
    - _Requirements: 15.3, 15.6_

- [ ] 19. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Backend uses Python/FastAPI, frontend uses TypeScript/Next.js 15, smart contracts use Rust/Soroban
- Checkpoints ensure incremental validation at key integration points
- Property tests validate universal correctness properties defined in the design
- Unit tests validate specific examples and edge cases
- Celery workers handle async OCR processing and Stellar transaction retries
- All sensitive data (wallet keys, documents) is encrypted at rest
