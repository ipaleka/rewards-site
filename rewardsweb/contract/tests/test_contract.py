"""Testing module for :py:mod:`contract.artifacts.contract` module."""

import os
import time
from pathlib import Path

import pytest
from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    AppCallParams,
    Arc56Contract,
    AssetTransferParams,
    LogicError,
    PaymentParams,
    SendParams,
    SigningAccount,
)
from algokit_utils.applications import AppClient, AppClientMethodCallParams
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    TransactionWithSigner,
)
from algosdk.error import AlgodHTTPError
from algosdk.transaction import AssetCreateTxn, OnComplete
from algosdk.v2client.algod import AlgodClient
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

dapp_name = os.getenv("REWARDS_DAPP_NAME")
token_id = os.getenv("REWARDS_TOKEN_ID_TESTNET")

# Assume tests are run from the project root
CONTRACT_PATH = Path(__file__).parent.parent / "artifacts"
APP_SPEC_PATH = CONTRACT_PATH / f"{dapp_name}.arc56.json"


@pytest.fixture(scope="session")
def app_spec() -> Arc56Contract:
    """Get the application specification from the compiled artifact."""
    import json

    spec = json.loads(APP_SPEC_PATH.read_text())
    for network in spec["networks"].values():
        if "appID" in network:
            network["appId"] = network.pop("appID")
    return Arc56Contract.from_dict(spec)


@pytest.fixture(scope="session")
def admin_account(algod_client: AlgodClient) -> SigningAccount:
    return algod_client.account.from_environment("ADMIN_TESTNET")


@pytest.fixture(scope="function")
def rewards_client(algod_client: AlgodClient, app_spec: Arc56Contract) -> AppClient:
    """Create an ApplicationClient for the rewards contract."""
    return AppClient.from_network(
        app_spec=app_spec, algorand=algod_client, app_name="rewards"
    )


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


def make_payment(admin_account, receiver, amount=200_000):
    algorand = AlgorandClient.from_environment()
    algorand.send.payment(
        PaymentParams(
            sender=admin_account.address,
            receiver=receiver,
            amount=AlgoAmount(micro_algo=amount),
            signer=admin_account.signer,
        ),
        SendParams(max_rounds_to_wait_for_confirmation=5, suppress_log=False),
    )


def make_transfer(admin_account, receiver, amount):
    algorand = AlgorandClient.from_environment()
    algorand.send.asset_transfer(
        AssetTransferParams(
            sender=admin_account.address,
            asset_id=token_id,
            amount=amount,
            receiver=receiver,
            signer=admin_account.signer,
        ),
        SendParams(max_rounds_to_wait_for_confirmation=5, suppress_log=False),
    )


class TestContractContractRewards:
    """Testing class for :py:mod:`contract.contract` classes."""

    @pytest.mark.skip(
        "Should setup a new contract for short expiration period prior to testing"
    )
    def test_contract_rewards_setup(
        self,
        rewards_client: AppClient,
        admin_account: SigningAccount,
    ) -> None:
        """Test the setup method."""
        amount = 1_000_000_000

        make_payment(admin_account, rewards_client.app_address)
        make_transfer(admin_account, rewards_client.app_address, amount)

        asset_id = create_asset(rewards_client.algorand.client.algod, admin_account)
        claim_duration = 3600  # 1 hour

        # Call the setup method
        rewards_client.send.call(
            AppClientMethodCallParams(
                method="setup",
                args=[asset_id, claim_duration],
                sender=admin_account.address,
                signer=admin_account.signer,
            )
        )
        # Verify the global state
        global_state = rewards_client.get_global_state()
        assert global_state["token_id"] == token_id
        assert global_state["claim_period_duration"] == claim_duration


class TestContractRewardsAddAllocations:
    """Testing class for :class:`contract.contract.Rewards` add_allocations method."""

    def test_contract_rewards_add_alocations_for_no_admin(
        self, rewards_client: AppClient, admin_account: SigningAccount
    ) -> None:
        amount = 1_000_000_000
        min_balance, fees = 200_000, 4000

        other_account = rewards_client.algorand.account.random()
        make_payment(admin_account, other_account.address, amount=min_balance + fees)

        user_account = rewards_client.algorand.account.random()
        make_payment(admin_account, user_account.address, amount=min_balance + fees)

        with pytest.raises(LogicError, match="Sender is not the admin"):
            rewards_client.send.call(
                AppClientMethodCallParams(
                    method="add_allocations",
                    args=[[user_account.address], [amount]],
                    sender=other_account.address,
                    signer=other_account.signer,
                    box_references=[user_account.address.encode()],
                    static_fee=AlgoAmount(micro_algo=2000),
                )
            )

        make_payment(other_account, admin_account.address, amount=101_000)
        make_payment(user_account, admin_account.address, amount=101_000)

    def test_contract_rewards_add_alocations_different_sizes(
        self, rewards_client: AppClient, admin_account: SigningAccount
    ) -> None:
        amount = 1_000_000_000
        min_balance, fees = 200_000, 4000

        user_account = rewards_client.algorand.account.random()
        make_payment(admin_account, user_account.address, amount=min_balance + fees)

        with pytest.raises(LogicError, match="Input arrays must have the same length"):
            rewards_client.send.call(
                AppClientMethodCallParams(
                    method="add_allocations",
                    args=[[user_account.address], [amount, amount]],
                    sender=admin_account.address,
                    signer=admin_account.signer,
                    box_references=[user_account.address.encode()],
                    static_fee=AlgoAmount(micro_algo=2000),
                )
            )

        make_payment(user_account, admin_account.address, amount=101_000)

    def test_contract_rewards_add_alocations_single_address_static_fee(
        self, rewards_client: AppClient, admin_account: SigningAccount
    ) -> None:
        amount = 1_000_000_000
        min_balance, fees = 200_000, 4000

        user_asset_info = rewards_client.algorand.client.algod.account_asset_info(
            admin_account.address, token_id
        )
        if user_asset_info["asset-holding"]["amount"] < amount:
            make_transfer(admin_account, rewards_client.app_address, amount)

        make_payment(admin_account, rewards_client.app_address)

        # Add an allocation for a new user
        user_account = rewards_client.algorand.account.random()
        make_payment(admin_account, user_account.address, amount=min_balance + fees)
        rewards_client.send.call(
            AppClientMethodCallParams(
                method="add_allocations",
                args=[[user_account.address], [amount]],
                sender=admin_account.address,
                signer=admin_account.signer,
                box_references=[user_account.address.encode()],
                static_fee=AlgoAmount(micro_algo=2000),
            )
        )

        rewards_client.send.call(
            AppClientMethodCallParams(
                method="claim",
                sender=user_account.address,
                signer=user_account.signer,
                box_references=[user_account.address.encode()],
                static_fee=AlgoAmount(micro_algo=3000),
                asset_references=[token_id],
            )
        )

        rewards_client.algorand.send.app_call(
            AppCallParams(
                sender=user_account.address,
                signer=user_account.signer,
                app_id=rewards_client.app_id,
                on_complete=OnComplete.ClearStateOC,
            )
        )
        make_payment(user_account, admin_account.address, amount=min_balance + 1_000)


class TestContractRewardsClaim:
    """Testing class for :class:`contract.contract.Rewards` claim method."""

    def test_contract_rewards_claim_new_user(
        self, rewards_client: AppClient, admin_account: SigningAccount
    ) -> None:
        amount = 1_000_000_000
        min_balance, fees = 200_000, 4000

        make_payment(admin_account, rewards_client.app_address)
        make_transfer(admin_account, rewards_client.app_address, amount)

        # Add an allocation for a new user
        user_account = rewards_client.algorand.account.random()
        make_payment(admin_account, user_account.address, amount=min_balance + fees)

        rewards_client.send.call(
            AppClientMethodCallParams(
                method="add_allocations",
                args=[[user_account.address], [amount]],
                sender=admin_account.address,
                signer=admin_account.signer,
                box_references=[user_account.address.encode()],
                static_fee=AlgoAmount(micro_algo=2000),
            )
        )
        rewards_client.send.call(
            AppClientMethodCallParams(
                method="claim",
                sender=user_account.address,
                signer=user_account.signer,
                box_references=[user_account.address.encode()],
                max_fee=AlgoAmount(micro_algo=10_000),
                asset_references=[token_id],
                account_references=[user_account.address],
                static_fee=AlgoAmount(micro_algo=3000),
            ),
            send_params=SendParams(cover_app_call_inner_transaction_fees=True),
        )

        # Verify the user received the asset
        user_asset_info = rewards_client.algorand.client.algod.account_asset_info(
            user_account.address, token_id
        )
        assert user_asset_info["asset-holding"]["amount"] == amount

        with pytest.raises(AlgodHTTPError, match="box not found"):
            rewards_client.algorand.client.algod.application_box_by_name(
                rewards_client.app_id, user_account.address.encode()
            )

    def test_contract_rewards_claim_opted_in_user(
        self, rewards_client: AppClient, admin_account: SigningAccount
    ) -> None:
        amount = 1_000_000_000
        min_balance, fees = 200_000, 4000

        make_payment(admin_account, rewards_client.app_address)
        make_transfer(admin_account, rewards_client.app_address, amount)

        # Add an allocation for a new user
        user_account = rewards_client.algorand.account.random()
        make_payment(admin_account, user_account.address, amount=min_balance + fees)

        # User opts into the asset
        rewards_client.algorand.send.asset_opt_in(
            AssetTransferParams(
                sender=user_account.address,
                asset_id=token_id,
                amount=0,
                receiver=user_account.address,
                signer=user_account.signer,
            )
        )

        rewards_client.send.call(
            AppClientMethodCallParams(
                method="add_allocations",
                args=[[user_account.address], [amount]],
                sender=admin_account.address,
                signer=admin_account.signer,
                box_references=[user_account.address.encode()],
                static_fee=AlgoAmount(micro_algo=3000),
            )
        )

        rewards_client.send.call(
            AppClientMethodCallParams(
                method="claim",
                sender=user_account.address,
                signer=user_account.signer,
                box_references=[user_account.address.encode()],
                static_fee=AlgoAmount(micro_algo=2000),
                asset_references=[token_id],
            )
        )

        # Verify the user received the asset
        user_asset_info = rewards_client.algorand.client.algod.account_asset_info(
            user_account.address, token_id
        )
        assert user_asset_info["asset-holding"]["amount"] == amount

        with pytest.raises(AlgodHTTPError, match="box not found"):
            rewards_client.algorand.client.algod.application_box_by_name(
                rewards_client.app_id, user_account.address.encode()
            )

    @pytest.mark.skip(
        "Should setup a new contract for short expiration period prior to testing"
    )
    def test_contract_rewards_reclaim_allocation(
        self, rewards_client: AppClient, admin_account: SigningAccount
    ) -> None:
        """Test reclaiming an expired allocation."""
        amount = 1_000_000_000

        make_payment(admin_account, rewards_client.app_address)
        make_transfer(admin_account, rewards_client.app_address, amount)

        user_account = rewards_client.algorand.account.random()
        rewards_client.send.call(
            AppClientMethodCallParams(
                method="add_allocations",
                args=[[user_account.address], [amount]],
                sender=admin_account.address,
                signer=admin_account.signer,
                box_references=[user_account.address.encode()],
                static_fee=AlgoAmount(micro_algo=2000),
            )
        )

        # Wait for the allocation to expire
        time.sleep(2)

        admin_asset_info = rewards_client.algorand.client.algod.account_asset_info(
            admin_account.address, token_id
        )
        current_amount = admin_asset_info["asset-holding"]["amount"]

        # Reclaim the allocation
        rewards_client.send.call(
            AppClientMethodCallParams(
                method="reclaim_allocation",
                args=[user_account.address],
                sender=admin_account.address,
                signer=admin_account.signer,
                box_references=[user_account.address.encode()],
                asset_references=[token_id],
            )
        )

        box = rewards_client.algorand.client.algod.application_box_by_name(
            rewards_client.app_id, user_account.address.encode()
        )
        assert box is None

        admin_asset_info = rewards_client.algorand.client.algod.account_asset_info(
            admin_account.address, token_id
        )
        assert admin_asset_info["asset-holding"]["amount"] == current_amount + amount

    def test_contract_rewards_reclaim_before_expiry_fails(
        self, rewards_client: AppClient, admin_account: SigningAccount
    ) -> None:
        amount = 1_000_000_000

        make_payment(admin_account, rewards_client.app_address)
        make_transfer(admin_account, rewards_client.app_address, amount)

        user_account = rewards_client.algorand.account.random()
        rewards_client.send.call(
            AppClientMethodCallParams(
                method="add_allocations",
                args=[[user_account.address], [amount]],
                sender=admin_account.address,
                signer=admin_account.signer,
                box_references=[user_account.address.encode()],
                static_fee=AlgoAmount(micro_algo=2000),
            )
        )

        with pytest.raises(LogicError, match="Claim period has not ended"):
            rewards_client.send.call(
                AppClientMethodCallParams(
                    method="reclaim_allocation",
                    args=[user_account.address],
                    sender=admin_account.address,
                    signer=admin_account.signer,
                    box_references=[user_account.address.encode()],
                )
            )
