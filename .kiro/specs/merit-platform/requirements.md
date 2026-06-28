# Requirements Document

## Introduction

Merit is an AI-assisted conditional funding platform that automates the end-to-end lifecycle of financial assistance programs — from program creation and recipient application, through AI-powered document verification and compliance evaluation, to blockchain-based fund disbursement via Stellar/Soroban smart contracts. The platform serves three primary user roles (Super Admin, Organization Admin, Recipient) and eliminates manual verification bottlenecks by establishing a transparent, auditable, automated funding pipeline.

## Glossary

- **Platform**: The Merit system as a whole, encompassing backend, frontend, and blockchain layers
- **Auth_Service**: The authentication and authorization component managing user identity, JWT tokens, and RBAC
- **Program_Service**: The component managing funding program lifecycle, configuration, and requirements
- **Verification_Service**: The component orchestrating document upload, OCR processing, and confidence-based verification decisions
- **Compliance_Engine**: The component evaluating recipient eligibility against program requirements using configurable rule chains
- **Funding_Service**: The component managing Stellar wallet operations, Soroban smart contract interactions, and fund disbursement
- **Notification_Service**: The component managing multi-channel notifications for system events
- **OCR_Engine**: The AI/OCR layer (EasyOCR/PaddleOCR) that extracts text and structured data from uploaded documents
- **Soroban_Contract**: The Rust smart contract deployed on the Stellar/Soroban network for on-chain fund management
- **Super_Admin**: Platform-level administrator with unrestricted access to all system functions
- **Org_Admin**: Organization administrator who creates and manages funding programs
- **Recipient**: End user who applies for funding programs and submits compliance documents
- **Funding_Pool**: A Stellar account holding funds allocated to a specific program for disbursement
- **Compliance_Evaluation**: The result of evaluating a recipient's eligibility against all program requirements
- **Confidence_Score**: A numeric value in [0.0, 1.0] representing the OCR engine's certainty about extracted data
- **Frontend**: The Next.js 15 web application providing the user interface

## Requirements

### Requirement 1: User Registration and Authentication

**User Story:** As a user, I want to register and authenticate with the platform, so that I can securely access features appropriate to my role.

#### Acceptance Criteria

1. WHEN a user submits a valid registration form with email, password, full name, and role, THE Auth_Service SHALL create a new user account and return authentication tokens
2. WHEN a user submits login credentials, THE Auth_Service SHALL validate the credentials and return a JWT access token (15-minute expiry) and refresh token (7-day expiry)
3. WHEN a user provides a valid refresh token, THE Auth_Service SHALL issue a new access token and rotate the refresh token
4. WHEN a user submits a password that does not meet complexity requirements (minimum 8 characters), THE Auth_Service SHALL reject the registration and return a descriptive error
5. WHEN a user attempts to register with an email already in use, THE Auth_Service SHALL reject the registration with a duplicate email error
6. IF a user fails login 5 times consecutively, THEN THE Auth_Service SHALL lock the account for 30 minutes
7. WHEN an Org_Admin registers, THE Auth_Service SHALL require an organization_id to associate the user with their organization
8. THE Auth_Service SHALL hash all passwords using bcrypt with cost factor 12 before storage

### Requirement 2: Role-Based Access Control

**User Story:** As a platform administrator, I want role-based access control enforced on all endpoints, so that users can only access resources appropriate to their role.

#### Acceptance Criteria

1. THE Platform SHALL enforce RBAC at the middleware level for every protected API endpoint
2. WHEN a Recipient attempts to access program creation or verification approval endpoints, THE Platform SHALL return a 403 Forbidden response
3. WHEN an Org_Admin attempts to access resources belonging to a different organization, THE Platform SHALL return a 403 Forbidden response
4. WHEN a Super_Admin accesses any endpoint, THE Platform SHALL grant unrestricted access
5. WHEN a request contains an expired or invalid JWT token, THE Platform SHALL return a 401 Unauthorized response
6. THE Platform SHALL validate the user's role against the endpoint's allowed roles on every request

### Requirement 3: Funding Program Management

**User Story:** As an Organization Admin, I want to create and manage funding programs with configurable requirements, so that I can administer financial assistance according to my organization's criteria.

#### Acceptance Criteria

1. WHEN an Org_Admin submits a valid program creation request, THE Program_Service SHALL create a program in DRAFT status with the specified name, description, funding amount, max recipients, requirements, and dates
2. WHEN an Org_Admin activates a DRAFT program, THE Program_Service SHALL transition the program status to ACTIVE
3. WHEN an Org_Admin pauses an ACTIVE program, THE Program_Service SHALL transition the program status to PAUSED
4. WHEN an Org_Admin resumes a PAUSED program, THE Program_Service SHALL transition the program status to ACTIVE
5. WHILE a program is in COMPLETED status, THE Program_Service SHALL allow transition only to ARCHIVED status
6. WHEN a program creation request specifies funding_amount_per_recipient less than or equal to zero, THE Program_Service SHALL reject the request with a validation error
7. WHEN a program creation request specifies max_recipients less than 1, THE Program_Service SHALL reject the request with a validation error
8. WHEN an end_date is provided, THE Program_Service SHALL validate that end_date is after start_date
9. WHEN an Org_Admin adds a requirement to a program, THE Program_Service SHALL store the requirement with its type, condition operator, condition value, mandatory flag, and verification frequency
10. THE Program_Service SHALL support the following requirement types: academic_gwa, enrollment_status, document_submission, milestone_completion, attendance, and custom

### Requirement 4: Recipient Application

**User Story:** As a recipient, I want to apply for available funding programs, so that I can receive financial assistance that I qualify for.

#### Acceptance Criteria

1. WHEN a Recipient submits an application to an ACTIVE program, THE Program_Service SHALL create an application record linking the recipient to the program
2. WHEN a Recipient attempts to apply to a program that is not ACTIVE, THE Program_Service SHALL reject the application with an appropriate error
3. WHEN a program has reached its max_recipients limit, THE Program_Service SHALL reject new applications with a capacity error
4. WHEN a Recipient applies to a program, THE Platform SHALL record the application timestamp and initial status

### Requirement 5: Document Upload and OCR Processing

**User Story:** As a recipient, I want to upload compliance documents and have them automatically processed, so that my eligibility can be evaluated without manual delays.

#### Acceptance Criteria

1. WHEN a Recipient uploads a document, THE Verification_Service SHALL validate the file type and size (maximum 10MB), store the encrypted file, and create a document record with PENDING status
2. WHEN a document is submitted for processing, THE Verification_Service SHALL extract text using the OCR_Engine and produce structured data with field identification
3. WHEN OCR processing completes, THE Verification_Service SHALL calculate a Confidence_Score in the range [0.0, 1.0] based on field completeness and OCR engine confidence
4. WHEN the Confidence_Score is greater than or equal to the program threshold, THE Verification_Service SHALL auto-verify the document
5. WHEN the Confidence_Score is below the program threshold, THE Verification_Service SHALL flag the document for manual review and notify the Org_Admin
6. WHEN an Org_Admin manually reviews a flagged document, THE Verification_Service SHALL update the document status to VERIFIED or REJECTED based on the admin's decision
7. IF document processing fails due to file corruption or unsupported format, THEN THE Verification_Service SHALL set the document status to PROCESSING_FAILED and notify the Recipient to re-upload
8. THE Verification_Service SHALL support the following document types: grade_slip, enrollment_form, certificate, transcript, id_document, report, and custom
9. THE Verification_Service SHALL encrypt all stored documents at rest using AES-256
10. WHEN the same document content is processed multiple times, THE OCR_Engine SHALL produce identical structured_data and confidence_score results

### Requirement 6: Compliance Evaluation

**User Story:** As an organization admin, I want recipient eligibility automatically evaluated against program requirements, so that compliance determination is consistent, auditable, and fast.

#### Acceptance Criteria

1. WHEN a compliance evaluation is triggered for a recipient and program, THE Compliance_Engine SHALL evaluate every program requirement against the recipient's verified submissions
2. WHEN all mandatory requirements pass, THE Compliance_Engine SHALL determine the recipient as ELIGIBLE
3. WHEN any mandatory requirement fails, THE Compliance_Engine SHALL determine the recipient as INELIGIBLE
4. WHEN some requirements lack verified submissions, THE Compliance_Engine SHALL determine the recipient as PENDING_VERIFICATION
5. WHEN some optional requirements pass but mandatory ones fail, THE Compliance_Engine SHALL determine the recipient as PARTIAL
6. THE Compliance_Engine SHALL evaluate conditions using the following operators: lte, gte, eq, neq, lt, gt, contains, exists, not_exists
7. WHEN the condition operator is a numeric comparison (lte, gte, lt, gt) and the actual value cannot be parsed as a number, THE Compliance_Engine SHALL evaluate the condition as failed (return false)
8. WHEN the condition operator is "exists", THE Compliance_Engine SHALL return true only if the actual value is not None and not an empty/whitespace string
9. WHEN the condition operator is "not_exists", THE Compliance_Engine SHALL return true only if the actual value is None or an empty/whitespace string
10. WHEN the condition operator is "eq" or "contains", THE Compliance_Engine SHALL perform case-insensitive string comparison
11. THE Compliance_Engine SHALL record each evaluation result with a timestamp and schedule the next evaluation based on requirement verification frequencies
12. WHEN a batch evaluation is triggered for a program, THE Compliance_Engine SHALL evaluate all recipients enrolled in that program

### Requirement 7: Fund Disbursement

**User Story:** As a platform operator, I want funds automatically disbursed to eligible recipients via the Stellar blockchain, so that payments are transparent, auditable, and tamper-proof.

#### Acceptance Criteria

1. WHEN a disbursement is requested for an ELIGIBLE recipient, THE Funding_Service SHALL verify the compliance evaluation, check pool balance, invoke the Soroban_Contract, execute the Stellar transfer, and record the transaction
2. WHEN the funding pool balance is less than the requested disbursement amount, THE Funding_Service SHALL reject the disbursement and log the attempt
3. WHEN the funding pool is paused, THE Funding_Service SHALL reject all disbursement requests for that program
4. WHEN a Stellar transaction is confirmed, THE Funding_Service SHALL decrement the pool balance by the exact disbursement amount and increment the program's total_funded field
5. WHEN a Stellar transaction fails, THE Funding_Service SHALL record the transaction with "failed" status and retry with exponential backoff (maximum 5 attempts over 15 minutes)
6. IF the Stellar network is unreachable, THEN THE Funding_Service SHALL create a transaction record with "pending" status and retry submission via a background job
7. WHEN a disbursement completes successfully, THE Funding_Service SHALL notify the Recipient with the amount and transaction hash
8. THE Funding_Service SHALL record every disbursement in the audit log with program_id, recipient_id, amount, and transaction hash

### Requirement 8: Stellar Wallet Management

**User Story:** As a recipient, I want a Stellar wallet created and managed for me, so that I can receive disbursed funds on the blockchain.

#### Acceptance Criteria

1. WHEN a Recipient requests wallet creation, THE Funding_Service SHALL generate a Stellar keypair and store the wallet information
2. THE Funding_Service SHALL ensure each user has at most one wallet (wallet uniqueness per user)
3. THE Funding_Service SHALL store wallet private keys in an encrypted vault, never in code or configuration files
4. WHEN an Org_Admin funds a program, THE Funding_Service SHALL create a funding pool account on the Stellar network and register it with the Soroban_Contract

### Requirement 9: Soroban Smart Contract Operations

**User Story:** As a platform architect, I want on-chain enforcement of funding rules via Soroban smart contracts, so that fund disbursement is transparent and tamper-proof.

#### Acceptance Criteria

1. WHEN a program is funded, THE Soroban_Contract SHALL store the program state with org_id, funding_amount, max_recipients, and Active status
2. WHEN a recipient is registered for a program, THE Soroban_Contract SHALL store the recipient state and increment the program's current_recipients count
3. WHEN a program has reached max_recipients, THE Soroban_Contract SHALL reject further recipient registrations
4. WHEN a verification is submitted, THE Soroban_Contract SHALL update the recipient's eligibility status and record the verification timestamp
5. WHEN release_funds is invoked for an eligible recipient, THE Soroban_Contract SHALL transfer the specified amount from the pool to the recipient's wallet and update total_disbursed
6. WHEN release_funds is invoked for a non-eligible recipient, THE Soroban_Contract SHALL reject the transaction
7. WHEN an organization pauses a program, THE Soroban_Contract SHALL block all disbursements until the program is resumed
8. THE Soroban_Contract SHALL require organization authorization for program management operations (create, pause, resume)

### Requirement 10: Notification Management

**User Story:** As a user, I want to receive timely notifications about important events, so that I can stay informed about my applications, verifications, and disbursements.

#### Acceptance Criteria

1. WHEN a document is verified, THE Notification_Service SHALL send a notification to the Recipient
2. WHEN a compliance evaluation determines eligibility, THE Notification_Service SHALL send a notification to the Recipient with the result
3. WHEN funds are released, THE Notification_Service SHALL send a notification to the Recipient with the amount and transaction details
4. WHEN a document requires manual review, THE Notification_Service SHALL send a notification to the Org_Admin
5. WHEN a user requests their notifications, THE Notification_Service SHALL return notifications with unread/read status
6. WHEN a user marks a notification as read, THE Notification_Service SHALL update the notification status

### Requirement 11: Audit Logging

**User Story:** As a Super Admin, I want a complete audit trail of all state-changing operations, so that I can investigate issues and maintain regulatory compliance.

#### Acceptance Criteria

1. THE Platform SHALL create an audit log entry for every state-changing operation, including user_id, action, resource_type, resource_id, details, IP address, and timestamp
2. WHEN a compliance evaluation is performed, THE Platform SHALL record the evaluation action and result in the audit log
3. WHEN funds are disbursed, THE Platform SHALL record the disbursement details in the audit log
4. WHEN a program status changes, THE Platform SHALL record the status transition in the audit log
5. THE Platform SHALL make audit logs immutable (append-only, no modification or deletion)
6. WHEN a Super_Admin queries the audit logs, THE Platform SHALL support filtering by user, action, resource type, and time range

### Requirement 12: Admin Dashboard and Analytics

**User Story:** As a Super Admin, I want a dashboard with platform-wide analytics, so that I can monitor system health, user activity, and funding program performance.

#### Acceptance Criteria

1. WHEN a Super_Admin accesses the admin dashboard, THE Platform SHALL display platform-wide analytics including total users, organizations, programs, and transactions
2. WHEN a Super_Admin views the user management interface, THE Platform SHALL list all users with their roles, organizations, and account status
3. WHEN a Super_Admin views the organization list, THE Platform SHALL display all organizations with their verification status and program counts
4. WHEN an Org_Admin accesses program analytics, THE Program_Service SHALL return metrics including current recipients, total funded amount, compliance rates, and disbursement history

### Requirement 13: Frontend User Interface

**User Story:** As a user, I want a responsive, mobile-first web interface with intuitive navigation, so that I can efficiently interact with the platform on any device.

#### Acceptance Criteria

1. THE Frontend SHALL implement a gold and white color scheme consistently across all pages
2. THE Frontend SHALL use a mobile-first responsive design that adapts to desktop, tablet, and mobile viewports
3. WHEN a user navigates to the platform, THE Frontend SHALL render the initial page using server-side rendering for fast load times
4. THE Frontend SHALL use TanStack Query with stale-while-revalidate caching for server state management
5. THE Frontend SHALL validate all form inputs using Zod schemas before submission
6. WHEN a user uploads a document, THE Frontend SHALL compress images client-side before sending to the API
7. THE Frontend SHALL implement code splitting per route for optimal bundle sizes

### Requirement 14: API Security and Performance

**User Story:** As a platform operator, I want the API protected against common attacks and performant under load, so that the platform is reliable and secure.

#### Acceptance Criteria

1. THE Platform SHALL enforce rate limiting of 100 requests per minute for authenticated users and 20 requests per minute for unauthenticated users
2. THE Platform SHALL use TLS 1.3 for all network communication
3. THE Platform SHALL prevent SQL injection via parameterized queries through the ORM layer
4. THE Platform SHALL validate file uploads using magic byte checking in addition to file extension validation
5. WHEN a request exceeds the rate limit, THE Platform SHALL return a 429 Too Many Requests response
6. THE Platform SHALL implement database connection pooling with a pool size of 20 and max overflow of 10
7. THE Platform SHALL use Redis caching for frequently accessed data including program details and user profiles
8. THE Platform SHALL paginate all list endpoints using cursor-based pagination for large datasets

### Requirement 15: Deployment and Infrastructure

**User Story:** As a DevOps engineer, I want the platform containerized and deployable via CI/CD, so that releases are consistent, automated, and reproducible.

#### Acceptance Criteria

1. THE Platform SHALL be containerized using Docker Compose with services for Nginx, Next.js, FastAPI, Celery worker, PostgreSQL, and Redis
2. THE Platform SHALL use Nginx as a reverse proxy handling TLS termination and routing frontend and API traffic
3. WHEN code is pushed to the main branch, THE Platform SHALL run the CI/CD pipeline: lint, test, build, integration test, security scan, and deploy
4. THE Platform SHALL run all Docker containers as non-root users
5. THE Platform SHALL manage secrets via environment variables (AWS Secrets Manager in production)
6. THE Platform SHALL scan dependencies for vulnerabilities in the CI pipeline

### Requirement 16: Concurrent Operation Safety

**User Story:** As a platform architect, I want protection against race conditions in critical operations, so that data integrity is maintained under concurrent access.

#### Acceptance Criteria

1. WHEN two disbursement requests arrive simultaneously for the same recipient and program, THE Funding_Service SHALL use database-level advisory locks to prevent double-spend
2. WHEN a concurrent disbursement is blocked by a lock, THE Funding_Service SHALL return a "disbursement in progress" error to the second request
3. THE Platform SHALL ensure that funding pool balance deductions are atomic operations

