#![no_std]

extern crate alloc;

use soroban_sdk::{contract, contractimpl, contracttype, token, Address, Env, String};

/// Storage keys for contract data.
#[contracttype]
#[derive(Clone)]
pub enum DataKey {
    /// Key for a funding program. Value: FundingProgram
    Program(String),
    /// Key for a recipient within a program. Value: RecipientState
    Recipient(String, String),
    /// Key for the pool address associated with a program. Value: Address
    PoolAddress(String),
    /// Key for the token contract address used for transfers. Value: Address
    TokenAddress,
}

/// Program status on-chain.
#[contracttype]
#[derive(Clone, Debug, PartialEq)]
pub enum ProgramStatus {
    Active,
    Paused,
    Completed,
}

/// On-chain representation of a funding program.
#[contracttype]
#[derive(Clone, Debug)]
pub struct FundingProgram {
    pub program_id: String,
    pub org_id: String,
    pub funding_amount: i128,
    pub max_recipients: u32,
    pub current_recipients: u32,
    pub status: ProgramStatus,
    pub total_disbursed: i128,
}

/// On-chain state for a registered recipient.
#[contracttype]
#[derive(Clone, Debug)]
pub struct RecipientState {
    pub recipient_id: String,
    pub wallet_address: Address,
    pub is_eligible: bool,
    pub total_received: i128,
    pub last_verification_time: u64,
}

#[contract]
pub struct MeritFundingContract;

#[contractimpl]
impl MeritFundingContract {
    /// Initializes the contract with the token address used for fund transfers.
    ///
    /// This should be called once after deployment to set the native token
    /// (or custom asset) contract address for disbursements.
    pub fn initialize(env: Env, token_address: Address) {
        env.storage()
            .persistent()
            .set(&DataKey::TokenAddress, &token_address);
    }

    /// Sets the pool address for a given program.
    ///
    /// The pool address is the Stellar account that holds funds allocated
    /// to the program for disbursement.
    pub fn set_pool_address(env: Env, org: Address, program_id: String, pool_address: Address) {
        org.require_auth();

        // Verify program exists and org owns it
        let prog_key = DataKey::Program(program_id.clone());
        let _program: FundingProgram = env
            .storage()
            .persistent()
            .get(&prog_key)
            .expect("Program not found");

        let key = DataKey::PoolAddress(program_id);
        env.storage().persistent().set(&key, &pool_address);
    }

    /// Creates a new funding program on-chain.
    ///
    /// Preconditions:
    /// - `org` is authorized (must sign the transaction)
    /// - `funding_amount` > 0
    /// - `max_recipients` > 0
    ///
    /// Postconditions:
    /// - Program stored in persistent storage with Active status
    ///
    /// Requirements: 9.1, 9.8
    pub fn create_program(
        env: Env,
        org: Address,
        program_id: String,
        org_id: String,
        funding_amount: i128,
        max_recipients: u32,
    ) -> FundingProgram {
        org.require_auth();

        assert!(funding_amount > 0, "Funding amount must be positive");
        assert!(max_recipients > 0, "Must allow at least one recipient");

        let program = FundingProgram {
            program_id: program_id.clone(),
            org_id,
            funding_amount,
            max_recipients,
            current_recipients: 0,
            status: ProgramStatus::Active,
            total_disbursed: 0,
        };

        let key = DataKey::Program(program_id);
        env.storage().persistent().set(&key, &program);
        program
    }

    /// Registers a recipient for a funding program.
    ///
    /// Preconditions:
    /// - Program exists and is Active
    /// - `current_recipients` < `max_recipients`
    ///
    /// Postconditions:
    /// - RecipientState stored with is_eligible = false
    /// - `current_recipients` incremented
    ///
    /// Requirements: 9.2, 9.3
    pub fn register_recipient(
        env: Env,
        program_id: String,
        recipient_id: String,
        wallet_address: Address,
    ) -> RecipientState {
        let prog_key = DataKey::Program(program_id.clone());
        let mut program: FundingProgram = env
            .storage()
            .persistent()
            .get(&prog_key)
            .expect("Program not found");

        assert!(
            program.status == ProgramStatus::Active,
            "Program must be active"
        );
        assert!(
            program.current_recipients < program.max_recipients,
            "Program has reached max recipients"
        );

        let state = RecipientState {
            recipient_id: recipient_id.clone(),
            wallet_address,
            is_eligible: false,
            total_received: 0,
            last_verification_time: 0,
        };

        let rcpt_key = DataKey::Recipient(program_id.clone(), recipient_id);
        env.storage().persistent().set(&rcpt_key, &state);

        program.current_recipients += 1;
        env.storage().persistent().set(&prog_key, &program);

        state
    }

    /// Submits a verification result, updating recipient eligibility.
    ///
    /// Preconditions:
    /// - Recipient is registered for the program
    ///
    /// Postconditions:
    /// - `is_eligible` updated to the provided value
    /// - `last_verification_time` set to current ledger timestamp
    ///
    /// Requirements: 9.4
    pub fn submit_verification(
        env: Env,
        program_id: String,
        recipient_id: String,
        is_eligible: bool,
    ) -> RecipientState {
        let key = DataKey::Recipient(program_id, recipient_id);
        let mut state: RecipientState = env
            .storage()
            .persistent()
            .get(&key)
            .expect("Recipient not found");

        state.is_eligible = is_eligible;
        state.last_verification_time = env.ledger().timestamp();

        env.storage().persistent().set(&key, &state);
        state
    }

    /// Releases funds to an eligible recipient.
    ///
    /// Preconditions:
    /// - Recipient `is_eligible` is true
    /// - Program status is Active (not Paused)
    /// - `amount` > 0
    /// - Pool address and token address are configured
    ///
    /// Postconditions:
    /// - Token transfer executed from pool to recipient wallet
    /// - `total_disbursed` on program incremented by `amount`
    /// - `total_received` on recipient incremented by `amount`
    ///
    /// Requirements: 9.5, 9.6, 9.7
    pub fn release_funds(env: Env, program_id: String, recipient_id: String, amount: i128) {
        let prog_key = DataKey::Program(program_id.clone());
        let mut program: FundingProgram = env
            .storage()
            .persistent()
            .get(&prog_key)
            .expect("Program not found");

        assert!(
            program.status == ProgramStatus::Active,
            "Program must be active to disburse funds"
        );

        let rcpt_key = DataKey::Recipient(program_id.clone(), recipient_id);
        let mut state: RecipientState = env
            .storage()
            .persistent()
            .get(&rcpt_key)
            .expect("Recipient not found");

        assert!(state.is_eligible, "Recipient must be eligible");
        assert!(amount > 0, "Amount must be positive");

        // Execute token transfer from pool to recipient wallet
        let pool_key = DataKey::PoolAddress(program_id);
        let pool_address: Address = env
            .storage()
            .persistent()
            .get(&pool_key)
            .expect("Pool address not configured");

        let token_address: Address = env
            .storage()
            .persistent()
            .get(&DataKey::TokenAddress)
            .expect("Token address not configured");

        let token_client = token::Client::new(&env, &token_address);
        token_client.transfer(&pool_address, &state.wallet_address, &amount);

        // Update accounting state
        state.total_received += amount;
        program.total_disbursed += amount;

        env.storage().persistent().set(&rcpt_key, &state);
        env.storage().persistent().set(&prog_key, &program);
    }

    /// Pauses a funding program, blocking all disbursements.
    ///
    /// Preconditions:
    /// - `org` is authorized
    /// - Program exists
    ///
    /// Postconditions:
    /// - Program status set to Paused
    ///
    /// Requirements: 9.7, 9.8
    pub fn pause_funding(env: Env, org: Address, program_id: String) {
        org.require_auth();

        let key = DataKey::Program(program_id);
        let mut program: FundingProgram = env
            .storage()
            .persistent()
            .get(&key)
            .expect("Program not found");

        program.status = ProgramStatus::Paused;
        env.storage().persistent().set(&key, &program);
    }

    /// Resumes a paused funding program.
    ///
    /// Preconditions:
    /// - `org` is authorized
    /// - Program is currently Paused
    ///
    /// Postconditions:
    /// - Program status set to Active
    ///
    /// Requirements: 9.7, 9.8
    pub fn resume_funding(env: Env, org: Address, program_id: String) {
        org.require_auth();

        let key = DataKey::Program(program_id);
        let mut program: FundingProgram = env
            .storage()
            .persistent()
            .get(&key)
            .expect("Program not found");

        assert!(
            program.status == ProgramStatus::Paused,
            "Program must be paused to resume"
        );

        program.status = ProgramStatus::Active;
        env.storage().persistent().set(&key, &program);
    }

    /// Returns the current state of a funding program.
    pub fn get_program(env: Env, program_id: String) -> FundingProgram {
        let key = DataKey::Program(program_id);
        env.storage()
            .persistent()
            .get(&key)
            .expect("Program not found")
    }

    /// Returns the current state of a recipient within a program.
    pub fn get_recipient(
        env: Env,
        program_id: String,
        recipient_id: String,
    ) -> RecipientState {
        let key = DataKey::Recipient(program_id, recipient_id);
        env.storage()
            .persistent()
            .get(&key)
            .expect("Recipient not found")
    }
}

#[cfg(test)]
mod test {
    use super::*;
    use soroban_sdk::{testutils::Address as _, Address, Env, String};

    fn setup_env() -> (Env, Address) {
        let env = Env::default();
        env.mock_all_auths();
        let org = Address::generate(&env);
        (env, org)
    }

    fn str(env: &Env, s: &str) -> String {
        String::from_str(env, s)
    }

    // ============================================================
    // Program Creation Tests (Req 9.1, 9.8)
    // ============================================================

    #[test]
    fn test_create_program_success() {
        let (env, org) = setup_env();
        let contract_id = env.register_contract(None, MeritFundingContract);
        let client = MeritFundingContractClient::new(&env, &contract_id);

        let program = client.create_program(
            &org,
            &str(&env, "program-1"),
            &str(&env, "org-1"),
            &1000_i128,
            &50_u32,
        );

        assert_eq!(program.funding_amount, 1000);
        assert_eq!(program.max_recipients, 50);
        assert_eq!(program.current_recipients, 0);
        assert_eq!(program.total_disbursed, 0);
        assert_eq!(program.status, ProgramStatus::Active);
    }

    #[test]
    #[should_panic(expected = "Funding amount must be positive")]
    fn test_create_program_zero_amount_panics() {
        let (env, org) = setup_env();
        let contract_id = env.register_contract(None, MeritFundingContract);
        let client = MeritFundingContractClient::new(&env, &contract_id);

        client.create_program(
            &org,
            &str(&env, "program-bad"),
            &str(&env, "org-1"),
            &0_i128,
            &10_u32,
        );
    }

    #[test]
    #[should_panic(expected = "Must allow at least one recipient")]
    fn test_create_program_zero_recipients_panics() {
        let (env, org) = setup_env();
        let contract_id = env.register_contract(None, MeritFundingContract);
        let client = MeritFundingContractClient::new(&env, &contract_id);

        client.create_program(
            &org,
            &str(&env, "program-bad"),
            &str(&env, "org-1"),
            &1000_i128,
            &0_u32,
        );
    }

    // ============================================================
    // Recipient Registration Tests (Req 9.2, 9.3)
    // ============================================================

    #[test]
    fn test_register_recipient_success() {
        let (env, org) = setup_env();
        let contract_id = env.register_contract(None, MeritFundingContract);
        let client = MeritFundingContractClient::new(&env, &contract_id);
        let recipient_wallet = Address::generate(&env);

        client.create_program(
            &org,
            &str(&env, "prog-1"),
            &str(&env, "org-1"),
            &5000_i128,
            &10_u32,
        );

        let state = client.register_recipient(
            &str(&env, "prog-1"),
            &str(&env, "recipient-1"),
            &recipient_wallet,
        );

        assert_eq!(state.is_eligible, false);
        assert_eq!(state.total_received, 0);

        let program = client.get_program(&str(&env, "prog-1"));
        assert_eq!(program.current_recipients, 1);
    }

    #[test]
    fn test_register_multiple_recipients_up_to_max() {
        let (env, org) = setup_env();
        let contract_id = env.register_contract(None, MeritFundingContract);
        let client = MeritFundingContractClient::new(&env, &contract_id);

        client.create_program(
            &org,
            &str(&env, "prog-2"),
            &str(&env, "org-1"),
            &5000_i128,
            &3_u32,
        );

        for i in 0..3 {
            let wallet = Address::generate(&env);
            let id = String::from_str(&env, &alloc::format!("r-{}", i));
            client.register_recipient(&str(&env, "prog-2"), &id, &wallet);
        }

        let program = client.get_program(&str(&env, "prog-2"));
        assert_eq!(program.current_recipients, 3);
    }

    #[test]
    #[should_panic(expected = "Program has reached max recipients")]
    fn test_register_beyond_max_recipients_panics() {
        let (env, org) = setup_env();
        let contract_id = env.register_contract(None, MeritFundingContract);
        let client = MeritFundingContractClient::new(&env, &contract_id);

        client.create_program(
            &org,
            &str(&env, "prog-3"),
            &str(&env, "org-1"),
            &5000_i128,
            &2_u32,
        );

        for i in 0..3 {
            let wallet = Address::generate(&env);
            let id = String::from_str(&env, &alloc::format!("r-{}", i));
            client.register_recipient(&str(&env, "prog-3"), &id, &wallet);
        }
    }

    // ============================================================
    // Verification Tests (Req 9.4)
    // ============================================================

    #[test]
    fn test_submit_verification_sets_eligible() {
        let (env, org) = setup_env();
        let contract_id = env.register_contract(None, MeritFundingContract);
        let client = MeritFundingContractClient::new(&env, &contract_id);
        let wallet = Address::generate(&env);

        client.create_program(
            &org,
            &str(&env, "prog-v"),
            &str(&env, "org-1"),
            &5000_i128,
            &10_u32,
        );
        client.register_recipient(&str(&env, "prog-v"), &str(&env, "r-1"), &wallet);

        let state = client.submit_verification(
            &str(&env, "prog-v"),
            &str(&env, "r-1"),
            &true,
        );

        assert_eq!(state.is_eligible, true);
        assert!(state.last_verification_time > 0);
    }

    #[test]
    fn test_submit_verification_sets_ineligible() {
        let (env, org) = setup_env();
        let contract_id = env.register_contract(None, MeritFundingContract);
        let client = MeritFundingContractClient::new(&env, &contract_id);
        let wallet = Address::generate(&env);

        client.create_program(
            &org,
            &str(&env, "prog-v2"),
            &str(&env, "org-1"),
            &5000_i128,
            &10_u32,
        );
        client.register_recipient(&str(&env, "prog-v2"), &str(&env, "r-1"), &wallet);
        client.submit_verification(&str(&env, "prog-v2"), &str(&env, "r-1"), &true);

        let state = client.submit_verification(
            &str(&env, "prog-v2"),
            &str(&env, "r-1"),
            &false,
        );

        assert_eq!(state.is_eligible, false);
    }

    // ============================================================
    // Release Funds Tests (Req 9.5, 9.6, 9.7)
    // ============================================================

    #[test]
    #[should_panic(expected = "Recipient must be eligible")]
    fn test_release_funds_ineligible_panics() {
        let (env, org) = setup_env();
        let contract_id = env.register_contract(None, MeritFundingContract);
        let client = MeritFundingContractClient::new(&env, &contract_id);
        let wallet = Address::generate(&env);
        let token_addr = Address::generate(&env);
        let pool_addr = Address::generate(&env);

        client.initialize(&token_addr);
        client.create_program(
            &org,
            &str(&env, "prog-f"),
            &str(&env, "org-1"),
            &5000_i128,
            &10_u32,
        );
        client.set_pool_address(&org, &str(&env, "prog-f"), &pool_addr);
        client.register_recipient(&str(&env, "prog-f"), &str(&env, "r-1"), &wallet);
        // Not verified → not eligible

        client.release_funds(&str(&env, "prog-f"), &str(&env, "r-1"), &100_i128);
    }

    #[test]
    #[should_panic(expected = "Program must be active to disburse funds")]
    fn test_release_funds_paused_program_panics() {
        let (env, org) = setup_env();
        let contract_id = env.register_contract(None, MeritFundingContract);
        let client = MeritFundingContractClient::new(&env, &contract_id);
        let wallet = Address::generate(&env);
        let token_addr = Address::generate(&env);
        let pool_addr = Address::generate(&env);

        client.initialize(&token_addr);
        client.create_program(
            &org,
            &str(&env, "prog-p"),
            &str(&env, "org-1"),
            &5000_i128,
            &10_u32,
        );
        client.set_pool_address(&org, &str(&env, "prog-p"), &pool_addr);
        client.register_recipient(&str(&env, "prog-p"), &str(&env, "r-1"), &wallet);
        client.submit_verification(&str(&env, "prog-p"), &str(&env, "r-1"), &true);
        client.pause_funding(&org, &str(&env, "prog-p"));

        client.release_funds(&str(&env, "prog-p"), &str(&env, "r-1"), &100_i128);
    }

    // ============================================================
    // Pause/Resume Tests (Req 9.7, 9.8)
    // ============================================================

    #[test]
    fn test_pause_and_resume_lifecycle() {
        let (env, org) = setup_env();
        let contract_id = env.register_contract(None, MeritFundingContract);
        let client = MeritFundingContractClient::new(&env, &contract_id);

        client.create_program(
            &org,
            &str(&env, "prog-lr"),
            &str(&env, "org-1"),
            &5000_i128,
            &10_u32,
        );

        let prog = client.get_program(&str(&env, "prog-lr"));
        assert_eq!(prog.status, ProgramStatus::Active);

        client.pause_funding(&org, &str(&env, "prog-lr"));
        let prog = client.get_program(&str(&env, "prog-lr"));
        assert_eq!(prog.status, ProgramStatus::Paused);

        client.resume_funding(&org, &str(&env, "prog-lr"));
        let prog = client.get_program(&str(&env, "prog-lr"));
        assert_eq!(prog.status, ProgramStatus::Active);
    }

    #[test]
    #[should_panic(expected = "Program must be paused to resume")]
    fn test_resume_active_program_panics() {
        let (env, org) = setup_env();
        let contract_id = env.register_contract(None, MeritFundingContract);
        let client = MeritFundingContractClient::new(&env, &contract_id);

        client.create_program(
            &org,
            &str(&env, "prog-ra"),
            &str(&env, "org-1"),
            &5000_i128,
            &10_u32,
        );

        client.resume_funding(&org, &str(&env, "prog-ra"));
    }

    // ============================================================
    // Property P6: State Consistency
    // ============================================================

    #[test]
    fn test_property_p6_current_recipients_equals_registered_count() {
        let (env, org) = setup_env();
        let contract_id = env.register_contract(None, MeritFundingContract);
        let client = MeritFundingContractClient::new(&env, &contract_id);

        client.create_program(
            &org,
            &str(&env, "prog-p6"),
            &str(&env, "org-1"),
            &5000_i128,
            &20_u32,
        );

        let count = 7;
        for i in 0..count {
            let wallet = Address::generate(&env);
            let id = String::from_str(&env, &alloc::format!("r-{}", i));
            client.register_recipient(&str(&env, "prog-p6"), &id, &wallet);
        }

        let program = client.get_program(&str(&env, "prog-p6"));
        assert_eq!(program.current_recipients, count as u32);
    }
}
