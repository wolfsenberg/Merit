# Merit: Scholarship Disbursement Without the "Pila" (Long Lines)

[![Merit Platform CI/CD](https://img.shields.io/badge/Merit%20Platform%20CI%2FCD-passing-brightgreen)](https://github.com/wolfsenberg/Merit/actions/workflows/ci.yml)
[![Stellar Network](https://img.shields.io/badge/Stellar-Testnet-blue)](https://stellar.expert/explorer/testnet)

## Roadmap and Requirements Checklist

| Level | Status | Features Implemented |
| :--- | :---: | :--- |
| **Level 1** | Done | Freighter wallet setup, Stellar testnet integration, wallet balance display, transaction history. |
| **Level 2** | Done | Soroban contract deployed, testnet contract evidence, frontend wallet flow, cashout demo flow, transaction visibility. |
| **Level 3** | Done | Functional mini-dApp demo for students and admins, smart contract tests, frontend build validation. |

---

> ### The Problem: Scholarship day should not cost students a school day.
>
> For many Filipino scholars, receiving financial assistance is supposed to help them stay in school. But in practice, claiming that scholarship can become another burden. Payout schedules are often announced on weekdays, during the same hours when government offices, schools, and campuses are active. Students are forced to line up, travel, wait, and sometimes miss class just to receive money that was meant to support their education.
>
> The problem becomes heavier when the payout date lands on an exam day, laboratory session, defense schedule, or graded activity. **"Paano mo mama-maintain ang mataas na grades kung kailangan mong umabsent para lang makuha ang allowance mo?"** ("How can you maintain high grades if you have to be absent just to claim your allowance?") A scholarship should reduce pressure, not create a choice between attendance and survival money.
>
> Delayed releases also make things worse. Students budget around expected stipends for food, transportation, rent, school supplies, and projects. When the money arrives late, or when claiming it requires long lines and manual processing, scholars are left anxious and financially stretched. The support exists, but the delivery system still feels slow, inconvenient, and unfair to the students who need it most.

---

### The Solution: Enter Merit, a Digital Scholarship Wallet and Conditional Funding Platform


**Desktop:** <img width="1887" height="974" alt="image" src="https://github.com/user-attachments/assets/75a81c1a-cede-42e8-bcc6-876b72bb1aae" />

**Mobile:** <img width="520" height="970" alt="image" src="https://github.com/user-attachments/assets/860a67f1-6c5b-4c9f-b302-72f674664f39" />


Merit is a scholarship disbursement platform built for students, schools, foundations, and government scholarship providers. It turns the scholarship release process into a wallet-based flow: scholars can receive, track, and cash out funds without needing to skip class, wait in long lines, or rely on manual payout schedules.

For admins, Merit provides a way to manage scholarship programs, review scholars, approve recipients, and release funds with clear records. For students, Merit feels familiar: connect a wallet, view available balance, cash out to GCash, Maya, or bank transfer, and see every transaction in one place.

Under the hood, Merit uses Stellar and Soroban smart contracts to make scholarship releases more transparent, programmable, and auditable. Funds can be tied to eligibility checks and program rules, giving institutions confidence that assistance is released only to approved scholars.

**Live App:** [https://merit-platform.vercel.app](https://merit-platform.vercel.app)

**Video Demo:** [Link to demo video]

**Pitch Document:** https://docs.google.com/document/d/1QGBxMLmTLBD-mrm6kra0BLmF624hGDq6nIGt92q4z1c/edit?usp=sharing

---

### Table of Contents
*   [Key Features](#key-features)
*   [The Vision](#the-vision)
*   [Tech Stack](#tech-stack)
*   [Smart Contract](#smart-contract)
*   [How Stellar Powers Merit](#how-stellar-powers-merit)
*   [Architecture and Structure](#architecture-and-structure)
*   [CI/CD Pipeline](#cicd-pipeline)
*   [Requirements Detail](#requirements-detail)
*   [Demo Flow](#demo-flow)
*   [Escrow Lifecycle](#escrow-lifecycle)
*   [Setup](#setup)

---

## Key Features

### 1. Student Wallet for Scholarship Funds
Students can view their available scholarship balance, see their transaction history, and cash out to familiar channels such as GCash, Maya, or bank transfer. The demo flow persists balances and cashout records per connected Freighter wallet.

### 2. No More "Absent Para Pumila" (Being Absent Just to Line Up)
Merit removes the need for students to physically line up during school hours just to claim scholarship funds. Payouts can be sent digitally, helping scholars avoid missing classes, exams, and important academic activities.

### 3. Admin Disbursement Records
Scholarship admins can approve scholars, send funds, and view disbursement records showing who received money, how much was sent, and the transaction reference.

### 4. Admin Review and Eligibility Tracking
Merit keeps the approval flow simple for the current demo: admins review scholars, mark eligible recipients, and release funds with visible records.

### 5. Familiarity and "Zero-Crypto Anxiety"
*   **Freighter Wallet Login**: Connect a Stellar wallet without exposing private keys.
*   **Local Currency Display**: Scholarship amounts are shown in PHP for student accessibility.
*   **Cashout Simulation**: Students interact with familiar cashout destinations like GCash, Maya, and bank transfer.
*   **Simple Records**: Transactions are displayed like an e-wallet history, not like a blockchain explorer.

### 6. Scholars Hub
Students can browse scholarship tips, share information, comment on posts, and raise concerns per scholarship program. This gives the platform a community and support layer beyond fund disbursement.

---

## The Vision: Why Philippines? Why Now?

Merit is designed for a country where scholarships can be life-changing, but payout logistics can still feel outdated. Many Filipino students rely on stipends for daily survival: "pamasahe" (transportation fare), meals, rent, printing, internet, and school materials. When the release process is delayed or inconvenient, the student carries the cost.

The vision is simple: scholarship support should arrive in a way that respects the student's time, attendance, and academic responsibilities. Merit turns financial assistance into **programmable, transparent, student-first capital**.

Instead of making scholars choose between class and claiming money, Merit lets funds move digitally, with rules, records, and accountability built in.

---

## Tech Stack

*   **Blockchain**: Stellar Soroban on Testnet
*   **Smart Contract**: Rust + soroban-sdk
*   **Frontend**: Next.js 15, TypeScript, Tailwind CSS, TanStack Query, Zustand
*   **Backend**: FastAPI, SQLAlchemy async, Pydantic v2
*   **Database**: PostgreSQL with Alembic migrations
*   **Cache and Jobs**: Redis, Celery/ARQ-ready worker architecture
*   **Wallet**: Freighter Wallet
*   **Testing**: pytest, Hypothesis property-based tests, Vitest
*   **Infrastructure**: Docker Compose, Nginx, GitHub Actions

---

## Smart Contract

**Contract ID (Testnet):** `CCTEUDESKDOVX2XT5OY4CYTFPVSYOXETBRNY6OW7Z36TEB2EWLELWKWF`

<!-- Smart contract screenshot placeholder -->
<!-- Stellar Expert deployment screenshot placeholder -->
<!-- Contract interaction screenshot placeholder -->
<!-- Demo transaction screenshot placeholder -->

| Item | Value |
|---|---|
| Contract Address | `CCTEUDESKDOVX2XT5OY4CYTFPVSYOXETBRNY6OW7Z36TEB2EWLELWKWF` |
| Deploy TX Hash | `ddf89015528d31eae82f2d0c3726966426b210fb4b3bca8d97f6e72775dbec53` |
| Contract Interaction TX | `24b3d1fed20a08a113f7daeb50ac747d39c39ade036cbab88eaf24b679ad4db7` |
| WASM Hash | `d2a20510fe179060724ddd8d8237c103ee4fcb48e5fa3f5176a9c5a6e2f6fa1c` |
| Network | Stellar Testnet |
| Deployer Account | `GBC2Q2YBDDQESKGRUKKJ4PKPJ7H7JG6D6CELW4AAKYMNCSVYPF5C5ECN` |

| Function | Description |
|---|---|
| `initialize` | Sets the token address used for funding transfers. |
| `create_program` | Creates a scholarship or assistance program on-chain. |
| `set_pool_address` | Connects a program to a funding pool account. |
| `register_recipient` | Registers a scholar wallet for a program. |
| `submit_verification` | Updates whether a scholar is eligible after verification. |
| `release_funds` | Releases funds to an eligible scholar wallet. |
| `pause_funding` | Pauses disbursements for a program. |
| `resume_funding` | Resumes disbursements for a program. |

<img width="1130" height="474" alt="Screenshot 2026-06-29 192745" src="https://github.com/user-attachments/assets/3f36ecf1-0be3-4806-b432-b33272cbf3da" />
<img width="1482" height="414" alt="Screenshot 2026-06-29 194526" src="https://github.com/user-attachments/assets/e37d8ec5-5c22-488a-a86d-ca6cd12dadab" />

**Verify on Stellar Expert:**
*   [View Contract](https://stellar.expert/explorer/testnet/contract/CCTEUDESKDOVX2XT5OY4CYTFPVSYOXETBRNY6OW7Z36TEB2EWLELWKWF)
*   [View Deploy Transaction](https://stellar.expert/explorer/testnet/tx/ddf89015528d31eae82f2d0c3726966426b210fb4b3bca8d97f6e72775dbec53)
*   [View Interaction Transaction](https://stellar.expert/explorer/testnet/tx/24b3d1fed20a08a113f7daeb50ac747d39c39ade036cbab88eaf24b679ad4db7)
*   [Stellar Lab](https://lab.stellar.org/r/testnet/contract/CCTEUDESKDOVX2XT5OY4CYTFPVSYOXETBRNY6OW7Z36TEB2EWLELWKWF)

---

## How Stellar Powers Merit

*   **Conditional Scholarship Release**: Soroban smart contracts can enforce that funds are released only after a scholar is registered and marked eligible.
*   **Transparent Program Accounting**: Program totals, recipient states, and disbursement records can be independently verified.
*   **Fast Settlement**: Stellar transactions settle quickly with low fees, making it practical for scholarship payouts.
*   **Wallet-Based Access**: Scholars can connect a wallet and receive funds without needing to understand private blockchain mechanics.
*   **Auditability for Institutions**: Scholarship providers can show where funds went, when they were released, and which program rules triggered the payout.

---

## Architecture and Structure

Merit follows a hybrid scholarship funding architecture:

1. **Frontend**: Next.js dashboard for students, organization admins, and super admins.
2. **Backend**: FastAPI service for authentication, programs, applications, notifications, wallets, and funding.
3. **Admin Review Layer**: Scholarship admins review scholars and update eligibility status.
4. **Stellar/Soroban Layer**: Smart contract state and disbursement logic for transparent scholarship release.
5. **Data Layer**: PostgreSQL, Redis, audit logs, and transaction records.

```text
merit/
|-- frontend/                 # Next.js student/admin interface
|   |-- src/app/               # App Router pages
|   |-- src/components/        # UI and layout components
|   |-- src/hooks/             # API and query hooks
|   `-- src/lib/               # Auth, Freighter, API client, demo ledger
|-- backend/                  # FastAPI backend
|   |-- app/api/v1/            # API endpoints
|   |-- app/models/            # SQLAlchemy models
|   |-- app/schemas/           # Pydantic schemas
|   |-- app/services/          # Business logic
|   |-- app/tasks/             # Background jobs
|   `-- tests/                 # Unit and property-based tests
|-- contracts/                # Soroban smart contracts
|   `-- merit-funding/         # Main funding contract
|-- docker/                   # Nginx and deployment configuration
|-- .github/workflows/        # CI/CD pipeline
`-- docker-compose.yml        # Multi-service orchestration
```

---

## CI/CD Pipeline

Merit uses GitHub Actions to keep the application buildable and testable:

*   **Backend CI**: Installs Python dependencies and validates FastAPI service tests.
*   **Frontend CI**: Installs Node dependencies and runs the Next.js build.
*   **Smart Contract CI**: Builds and tests the Soroban contract workspace.
*   **Continuous Deployment Ready**: The project is structured for deployment through Vercel for frontend, Render/Fly/Railway for backend, and Soroban testnet/mainnet for contracts.

---

## Requirements Detail

### Level 3: Mini-dApp Evidence

Merit is a functional scholarship funding mini-dApp. The core smart contract and demo flows support:

1.  `test_create_program_success`: Verifies successful on-chain program creation.
2.  `test_register_recipient_success`: Verifies recipient registration for a funding program.
3.  `test_submit_verification_sets_eligible`: Verifies eligibility updates after admin review.
4.  `test_release_funds_ineligible_panics`: Ensures funds cannot be released to ineligible recipients.

### Supporting Tests and Validation

Merit uses property-based testing to validate critical funding and access-control behavior:

| Property | Description |
|---|---|
| Funding Integrity | No transaction should overdraw a funding pool. |
| Eligibility Prerequisite | Funds should never be released without an eligible evaluation. |
| Eligibility Review Consistency | Eligible status should follow the platform's review rules. |
| Smart Contract State Consistency | Program totals should match recorded releases. |
| Audit Trail Completeness | Important state changes should create audit entries. |
| Role-Based Access Control | Users should only access actions allowed by their role. |
| Wallet Uniqueness | Each user should have at most one Stellar wallet. |
| Program Lifecycle | Program status transitions should follow valid lifecycle rules. |

---

## Demo Flow

1.  **Onboarding and Wallet Connection**: Connect Freighter and enter the student or admin demo.
2.  **Student Dashboard**: View available scholarship balance and recent transactions.
3.  **Cashout**: Select GCash, Maya, or bank transfer. Enter valid account details and confirm the transfer.
4.  **Transaction History**: See the cashout recorded and the available balance reduced after reload.
5.  **Scholars Hub**: Browse scholarship posts, add comments, and raise concerns per scholarship program.
6.  **Admin Flow**: Open the scholarship management page, approve pending scholars, and view the disbursement records.
7.  **Blockchain Verification**: Review the deployed Soroban contract and testnet transactions on Stellar Expert.

---

## Escrow Lifecycle

Merit is a conditional scholarship escrow and disbursement system:

1.  **Program Creation**: An organization creates a scholarship program with amount and recipient limits.
2.  **Funding Pool Setup**: Funds are assigned to a program pool.
3.  **Scholar Registration**: A scholar wallet is registered for the program.
4.  **Eligibility Review**: Admins review the scholar and mark the recipient eligible when approved.
5.  **Eligibility Trigger**: A scholar is marked eligible only after requirements pass.
6.  **Release**: The smart contract releases funds to the eligible scholar wallet.
7.  **Cashout**: The scholar can move funds from their Merit wallet flow to GCash, Maya, or bank transfer.
8.  **Record Keeping**: Admins and scholars can review transaction history and disbursement records.

---

## Setup

```bash
# Smart Contract Build and Test
cd contracts
cargo test
cargo build --target wasm32-unknown-unknown --release

# Frontend
cd frontend
npm install
npm run dev

# Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Docker Setup

```bash
cp .env.example .env
docker compose up -d
```

### Test Commands

```bash
# Backend
cd backend
pytest tests/ -v

# Frontend
cd frontend
npm run test -- --run

# Smart Contract
cd contracts
cargo test
```

---

*Merit: Scholarship support should reach students without making them miss the very education it is meant to protect.*
