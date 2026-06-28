#!/usr/bin/env bash
#
# deploy-testnet.sh
#
# Deploys the Merit Funding Soroban smart contract to the Stellar testnet.
#
# Prerequisites:
#   - Soroban CLI installed (stellar/soroban-cli)
#   - Rust toolchain with wasm32-unknown-unknown target
#   - A funded testnet account (use `soroban keys generate` + Friendbot)
#
# Usage:
#   ./scripts/deploy-testnet.sh [deployer-identity]
#
# Example:
#   ./scripts/deploy-testnet.sh my-deployer
#
# Environment variables:
#   SOROBAN_NETWORK_PASSPHRASE - Network passphrase (defaults to testnet)
#   SOROBAN_RPC_URL           - RPC endpoint (defaults to testnet)
#

set -euo pipefail

# --- Configuration ---
NETWORK="testnet"
RPC_URL="${SOROBAN_RPC_URL:-https://soroban-testnet.stellar.org}"
NETWORK_PASSPHRASE="${SOROBAN_NETWORK_PASSPHRASE:-Test SDF Network ; September 2015}"
CONTRACT_WASM="target/wasm32-unknown-unknown/release/merit_funding.wasm"
DEPLOYER_IDENTITY="${1:-deployer}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== Merit Funding Contract - Testnet Deployment ==="
echo ""
echo "Network:    $NETWORK"
echo "RPC URL:    $RPC_URL"
echo "Deployer:   $DEPLOYER_IDENTITY"
echo ""

# --- Step 1: Build the contract ---
echo "[1/4] Building contract..."
cd "$PROJECT_DIR"
soroban contract build --package merit-funding
echo "       Build complete: $CONTRACT_WASM"
echo ""

# --- Step 2: Optimize WASM (optional but recommended) ---
echo "[2/4] Optimizing WASM..."
if command -v soroban &> /dev/null; then
    soroban contract optimize --wasm "$CONTRACT_WASM"
    OPTIMIZED_WASM="${CONTRACT_WASM%.wasm}.optimized.wasm"
    if [ -f "$OPTIMIZED_WASM" ]; then
        CONTRACT_WASM="$OPTIMIZED_WASM"
        echo "       Optimized WASM: $CONTRACT_WASM"
    fi
else
    echo "       Skipping optimization (soroban CLI not found)"
fi
echo ""

# --- Step 3: Generate deployer identity if not exists ---
echo "[3/4] Checking deployer identity..."
if ! soroban keys address "$DEPLOYER_IDENTITY" &> /dev/null 2>&1; then
    echo "       Generating new identity: $DEPLOYER_IDENTITY"
    soroban keys generate "$DEPLOYER_IDENTITY" --network "$NETWORK"

    echo "       Funding account via Friendbot..."
    DEPLOYER_ADDRESS=$(soroban keys address "$DEPLOYER_IDENTITY")
    curl -s "https://friendbot.stellar.org?addr=$DEPLOYER_ADDRESS" > /dev/null
    echo "       Account funded: $DEPLOYER_ADDRESS"
else
    DEPLOYER_ADDRESS=$(soroban keys address "$DEPLOYER_IDENTITY")
    echo "       Using existing identity: $DEPLOYER_ADDRESS"
fi
echo ""

# --- Step 4: Deploy contract ---
echo "[4/4] Deploying contract to testnet..."
CONTRACT_ID=$(soroban contract deploy \
    --wasm "$CONTRACT_WASM" \
    --source "$DEPLOYER_IDENTITY" \
    --network "$NETWORK" \
    --rpc-url "$RPC_URL" \
    --network-passphrase "$NETWORK_PASSPHRASE")

echo ""
echo "=== Deployment Successful ==="
echo ""
echo "Contract ID: $CONTRACT_ID"
echo "Deployer:    $DEPLOYER_ADDRESS"
echo "Network:     $NETWORK"
echo ""
echo "Save this contract ID for use in your application configuration."
echo ""

# Write contract ID to a file for programmatic access
OUTPUT_FILE="$PROJECT_DIR/.deployed-contract-id"
echo "$CONTRACT_ID" > "$OUTPUT_FILE"
echo "Contract ID written to: $OUTPUT_FILE"
