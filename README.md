# Merit Platform

AI-assisted conditional funding platform that automates the end-to-end lifecycle of financial assistance programs — from program creation and recipient application, through AI-powered document verification and compliance evaluation, to blockchain-based fund disbursement via Stellar/Soroban smart contracts.

![Merit Platform](https://img.shields.io/badge/status-active-brightgreen) ![Tests](https://img.shields.io/badge/tests-480%2B%20passing-green) ![License](https://img.shields.io/badge/license-MIT-blue)

## Live Demo

- **Frontend**: [https://merit-platform.vercel.app](https://merit-platform.vercel.app) *(deploy with `vercel` CLI)*
- **Contract Address**: [`CDGVQGO635OJN3ZYG3VAMFUUHL6BY7W47U4DWOCSGQX2GQRMDJHTQFF7`](https://stellar.expert/explorer/testnet/contract/CDGVQGO635OJN3ZYG3VAMFUUHL6BY7W47U4DWOCSGQX2GQRMDJHTQFF7)
- **Deploy Transaction**: [`5e9715d7dd5ad1636d8fd17f5c22f2d4b16125063cc8a7d2564dfbbf54ec262f`](https://stellar.expert/explorer/testnet/tx/5e9715d7dd5ad1636d8fd17f5c22f2d4b16125063cc8a7d2564dfbbf54ec262f)
- **Contract Interaction TX**: [`d46785c4b9c41a94e02d2403c0e11b0d0c3fc2830e58dbeab6409d588c0c82a3`](https://stellar.expert/explorer/testnet/tx/d46785c4b9c41a94e02d2403c0e11b0d0c3fc2830e58dbeab6409d588c0c82a3)
- **Demo Video**: [Link to demo video] *(record 1-2 min walkthrough)*

## Features

### For Organization Admins
- Create and manage funding programs with configurable requirements
- AI-powered document verification with OCR (EasyOCR)
- Automated compliance evaluation engine with 9 condition operators
- Real-time analytics dashboard with disbursement tracking
- Manual review queue for low-confidence documents

### For Recipients
- Browse and apply to active funding programs
- Upload compliance documents with drag-and-drop
- Track application status and eligibility in real-time
- Stellar wallet management for fund receipt
- Notification system for updates

### For Super Admins
- Platform-wide analytics (users, orgs, programs, transactions)
- Audit log viewer with filtering (user, action, resource, time range)
- User and organization management

### Platform Capabilities
- **AI/OCR Pipeline**: EasyOCR-based document processing with confidence scoring
- **Blockchain**: Soroban smart contracts on Stellar for tamper-proof fund disbursement
- **Security**: AES-256-GCM encryption, bcrypt password hashing, JWT auth, Redis rate limiting
- **Property-Based Testing**: 8 formal correctness properties verified with Hypothesis

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query, Zustand |
| Backend | Python 3.13, FastAPI, SQLAlchemy (async), Pydantic v2 |
| Database | PostgreSQL with Alembic migrations |
| Cache | Redis (rate limiting, session storage) |
| AI/ML | EasyOCR, pattern-based field extraction |
| Blockchain | Stellar/Soroban, Rust smart contracts |
| Infrastructure | Docker Compose, Nginx, GitHub Actions CI/CD |
| Testing | pytest + Hypothesis (PBT), Vitest (frontend) |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js 15)                     │
├─────────────────────────────────────────────────────────────┤
│                      Nginx (Reverse Proxy)                    │
├─────────────────────────────────────────────────────────────┤
│                     Backend (FastAPI)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │   Auth   │ │ Programs │ │  Verify  │ │  Compliance  │  │
│  │ Service  │ │ Service  │ │ Service  │ │   Engine     │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ Funding  │ │  Wallet  │ │  Notify  │ │    Audit     │  │
│  │ Service  │ │ Service  │ │ Service  │ │   Service    │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL │ Redis │ File Storage │ Stellar Network         │
└─────────────────────────────────────────────────────────────┘
```

## Getting Started

### Prerequisites
- Python 3.13+
- Node.js 20+
- Docker & Docker Compose
- Rust + Soroban CLI (for smart contract development)

### Quick Start with Docker

```bash
# Clone the repository
git clone https://github.com/wolfsenberg/Merit.git
cd Merit

# Copy environment variables
cp .env.example .env

# Start all services
docker compose up -d

# Access the application
# Frontend: http://localhost:3000
# API: http://localhost:8000/api/v1/status
```

### Local Development

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Smart Contracts:**
```bash
cd contracts
cargo build --target wasm32-unknown-unknown --release

# Deploy to Soroban testnet
./scripts/deploy-testnet.sh
```

## Running Tests

### Backend (480+ tests with property-based testing)
```bash
cd backend
pip install pytest pytest-asyncio hypothesis httpx
pytest tests/ -v
```

### Frontend (Vitest)
```bash
cd frontend
npm run test -- --run
```

### Smart Contract
```bash
cd contracts
cargo test
```

## Property-Based Tests (Formal Correctness Properties)

The platform verifies 8 formal correctness properties using Hypothesis:

| Property | Description | Requirements |
|----------|-------------|--------------|
| P1: Funding Integrity | No transaction overdraws a funding pool | 7.1, 7.2, 7.4 |
| P2: Eligibility Prerequisite | Funds never released without ELIGIBLE evaluation | 7.1, 7.4 |
| P3: Verification Completeness | ELIGIBLE implies all mandatory requirements pass | 6.2, 6.3 |
| P4: Document Processing Determinism | Same content → identical structured data & confidence | 5.10 |
| P5: Condition Evaluation Consistency | Operators satisfy mathematical relationships | 6.6-6.10 |
| P6: Smart Contract State Consistency | total_disbursed = sum of releases | 9.1-9.8 |
| P7: Audit Trail Completeness | Every state change produces an audit entry | 11.1-11.4 |
| P8: Role-Based Access Control | Access correctly granted/denied per role | 2.1-2.6 |
| P9: Wallet Uniqueness | Each user has at most one wallet | 8.2 |
| P10: Program Status Lifecycle | Transitions follow valid lifecycle graph | 3.2-3.5 |

## API Documentation

The API is auto-documented via FastAPI's OpenAPI integration:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | User registration |
| POST | `/api/v1/auth/login` | User login (JWT) |
| GET/POST | `/api/v1/programs` | List/create programs |
| POST | `/api/v1/applications` | Submit application |
| POST | `/api/v1/documents/upload` | Upload document |
| POST | `/api/v1/compliance/evaluate` | Trigger evaluation |
| POST | `/api/v1/funding/disburse` | Disburse funds |
| GET | `/api/v1/notifications` | Get notifications |
| GET | `/api/v1/admin/audit-logs` | Query audit logs |

## Deployment

### Vercel (Frontend)
```bash
cd frontend
npx vercel --prod
```

### Soroban Testnet (Smart Contract)
```bash
cd contracts
soroban contract deploy \
  --wasm target/wasm32-unknown-unknown/release/merit_funding.wasm \
  --source YOUR_SECRET_KEY \
  --rpc-url https://soroban-testnet.stellar.org \
  --network-passphrase "Test SDF Network ; September 2015"
```

## Project Structure

```
merit-platform/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/v1/         # API routes
│   │   ├── core/           # Config, DB, Redis, Security
│   │   ├── middleware/     # Auth, Rate limiting
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── tasks/          # Background jobs
│   └── tests/              # 480+ tests
├── frontend/               # Next.js 15 frontend
│   └── src/
│       ├── app/            # App Router pages
│       ├── components/     # UI components
│       ├── hooks/          # TanStack Query hooks
│       └── lib/            # Utilities, API client
├── contracts/              # Soroban smart contracts
│   └── merit-funding/      # Main funding contract
├── docker/                 # Docker configs
├── .github/workflows/      # CI/CD pipeline
└── docker-compose.yml      # Multi-service orchestration
```

## Environment Variables

See `.env.example` for all required configuration. Key variables:

| Variable | Description |
|----------|-------------|
| `JWT_SECRET_KEY` | Secret for signing JWT tokens |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `WALLET_ENCRYPTION_KEY` | AES-256 key for wallet encryption (base64) |
| `STELLAR_NETWORK` | `testnet` or `mainnet` |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.
