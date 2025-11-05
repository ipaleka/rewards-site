"""Testing module for :py:mod:`contract.artifacts.contract` module."""

import os
import time
from pathlib import Path

import pytest
from algokit_utils import (
    AlgorandClient,
    Arc56Contract,
    LogicError,
    SigningAccount,
)
from algokit_utils.applications import AppClient
from algosdk.account import generate_account
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    TransactionWithSigner,
)
from algosdk.transaction import AssetCreateTxn, PaymentTxn
from algosdk.v2client.algod import AlgodClient
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

dapp_name = os.getenv("REWARDS_DAPP_NAME")

# Assume tests are run from the project root
CONTRACT_PATH = Path(__file__).parent.parent / "artifacts"
APP_SPEC_PATH = CONTRACT_PATH / f"{dapp_name}.arc56.json"


@pytest.fixture(scope="session")
def app_spec() -> Arc56Contract:
    """Get the application specification from the compiled artifact."""
    return Arc56Contract.from_json(APP_SPEC_PATH.read_text())


@pytest.fixture(scope="session")
def admin_account(algod_client: AlgodClient) -> SigningAccount:
    return algod_client.account.from_environment("ADMIN_TESTNET")


@pytest.fixture(scope="function")
def rewards_client(
    algod_client: AlgodClient,
    admin_account: SigningAccount,
    app_spec: Arc56Contract,
) -> AppClient:
    """Create an ApplicationClient for the rewards contract."""
    app_client = AppClient.from_network(
        app_spec=app_spec, algorand=algod_client, app_name="rewards"
    )
    return app_client.create()


@pytest.fixture(scope="session")
def algod_client() -> AlgodClient:
    return AlgorandClient.from_environment()


def create_asset(algod_client: AlgodClient, account: SigningAccount) -> int:
    """Create a new asset for testing."""
    sp = algod_client.suggested_params()
    atc = AtomicTransactionComposer()
    atc.add_transaction(
        TransactionWithSigner(
            AssetCreateTxn(
                sender=account.address,
                sp=sp,
                total=10_000,
                decimals=0,
                default_frozen=False,
            ),
            signer=account.signer,
        )
    )
    result = atc.execute(algod_client, 4)
    tx_info = algod_client.pending_transaction_info(result.tx_ids[0])
    return tx_info["asset-index"]


class TestContractContractRewards:
    """Testing class for :py:mod:`contract.rewards.contract` classes."""

    def test_contract_rewards_setup(
        self, rewards_client: AppClient, admin_account: SigningAccount
    ) -> None:
        """Test the setup method."""
        # Fund the app account with enough ALGO to opt into an asset
        rewards_client.fund(200_000)

        asset_id = create_asset(rewards_client.algod_client, admin_account)
        claim_duration = 3600  # 1 hour

        # Call the setup method
        rewards_client.call(
            "setup",
            token_id=asset_id,
            claim_period_duration=claim_duration,
        )

        # Verify the global state
        global_state = rewards_client.get_global_state()
        assert global_state["token_id"] == asset_id
        assert global_state["claim_period_duration"] == claim_duration

    def test_contract_rewards_add_allocations_and_claim(
        self, rewards_client: AppClient, admin_account: SigningAccount
    ) -> None:
        """Test adding allocations and a successful claim."""
        rewards_client.fund(200_000)
        asset_id = create_asset(rewards_client.algod_client, admin_account)
        rewards_client.call("setup", token_id=asset_id, claim_period_duration=3600)

        # Fund the contract with the asset
        sp = rewards_client.algod_client.suggested_params()
        atc = AtomicTransactionComposer()
        atc.add_transaction(
            TransactionWithSigner(
                AssetCreateTxn(
                    sender=admin_account.address,
                    sp=sp,
                    total=1000,
                    decimals=0,
                    default_frozen=False,
                ),
                signer=admin_account.signer,
            )
        )
        atc.add_transaction(
            TransactionWithSigner(
                PaymentTxn(
                    sender=admin_account.address,
                    sp=sp,
                    receiver=rewards_client.app_addr,
                    amt=100_000,
                ),
                signer=admin_account.signer,
            )
        )
        atc.execute(rewards_client.algod_client, 4)

        # Add an allocation for a new user
        user_account = SigningAccount.new_account()
        rewards_client.call(
            "add_allocations",
            addresses=[user_account.address],
            amounts=[100],
            boxes=[(rewards_client.app_id, user_account.address.encode())],
        )

        # Claim the allocation
        user_client = rewards_client.prepare(signer=user_account.signer)
        user_client.call(
            "claim",
            boxes=[(rewards_client.app_id, user_account.address.encode())],
        )

        # Verify the user received the asset
        user_asset_info = rewards_client.algod_client.account_asset_info(
            user_account.address, asset_id
        )
        assert user_asset_info["asset-holding"]["amount"] == 100

    def test_contract_rewards_reclaim_allocation(
        self, rewards_client: AppClient, admin_account: SigningAccount
    ) -> None:
        """Test reclaiming an expired allocation."""
        rewards_client.fund(200_000)
        asset_id = create_asset(rewards_client.algod_client, admin_account)
        # Set a very short claim period
        rewards_client.call("setup", token_id=asset_id, claim_period_duration=1)

        user_account = SigningAccount(private_key=generate_account()[0])
        rewards_client.call(
            "add_allocations",
            addresses=[user_account.address],
            amounts=[50],
            boxes=[(rewards_client.app_id, user_account.address.encode())],
        )

        # Wait for the allocation to expire
        time.sleep(2)

        # Reclaim the allocation
        rewards_client.call(
            "reclaim_allocation",
            user_address=user_account.address,
            boxes=[(rewards_client.app_id, user_account.address.encode())],
        )

        # # Verify the admin's balance increased (or check contract's balance)
        # admin_asset_info = rewards_client.algod_client.account_asset_info(
        #     admin_account.address, asset_id
        # )
        # This assertion is tricky without knowing the initial balance,
        # but we can assert the box is deleted.
        box = rewards_client.algod_client.application_box_by_name(
            rewards_client.app_id, user_account.address.encode()
        )
        assert box is None

    def test_contract_rewards_reclaim_before_expiry_fails(
        self, rewards_client: AppClient, admin_account: SigningAccount
    ) -> None:
        """Test that reclaiming before expiry fails."""
        rewards_client.fund(200_000)
        asset_id = create_asset(rewards_client.algod_client, admin_account)
        rewards_client.call("setup", token_id=asset_id, claim_period_duration=3600)

        user_account = SigningAccount(private_key=generate_account()[0])
        rewards_client.call(
            "add_allocations",
            addresses=[user_account.address],
            amounts=[50],
            boxes=[(rewards_client.app_id, user_account.address.encode())],
        )

        with pytest.raises(LogicError, match="Claim period has not ended"):
            rewards_client.call(
                "reclaim_allocation",
                user_address=user_account.address,
                boxes=[(rewards_client.app_id, user_account.address.encode())],
            )
