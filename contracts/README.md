# Merit Funding - Soroban Smart Contracts

Soroban smart contracts for the Merit conditional funding platform, deployed on the Stellar network.

## Structure

```
contracts/
├── Cargo.toml              # Workspace root
├── merit-funding/          # Main contract crate
│   ├── Cargo.toml
│   └── src/
│       └── lib.rs          # Contract implementation
└── scripts/
    └── deploy-testnet.sh   # Testnet deployment script
```

## Prerequisites

- [Rust](https://rustup.rs/) with `wasm32-unknown-unknown` target
- [Soroban CLI](https://soroban.stellar.org/docs/getting-started/setup)

```bash
# Install the WASM target
rustup target add wasm32-unknown-unknown

# Install Soroban CLI
cargo install --locked soroban-cli
```

## Build

```bash
cd contracts
soroban contract build --package merit-funding
```

## Test

```bash
cd contracts
cargo test
```

## Deploy to Testnet

```bash
cd contracts
./scripts/deploy-testnet.sh [deployer-identity]
```

The script will:
1. Build the contract WASM
2. Optimize the binary
3. Generate a deployer identity (if needed) and fund via Friendbot
4. Deploy to Stellar testnet

The deployed contract ID is saved to `.deployed-contract-id`.

## Contract Functions

| Function | Description |
|----------|-------------|
| `create_program` | Creates a new funding program on-chain |
| `register_recipient` | Registers a recipient for a program |
| `submit_verification` | Updates recipient eligibility status |
| `release_funds` | Disburses funds to an eligible recipient |
| `pause_funding` | Pauses a program (blocks disbursements) |
| `resume_funding` | Resumes a paused program |
