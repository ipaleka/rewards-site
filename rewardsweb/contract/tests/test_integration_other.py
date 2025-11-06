"""Rewards smart contract integration tests module."""

import pytest
from algokit_utils import (
    Account,
    ApplicationClient,
    ApplicationSpecification,
    get_localnet_default_account,
)
from algosdk.atomic_transaction_composer import AtomicTransactionComposer
from algosdk.v2client.algod import AlgodClient

from contract.contract import Rewards


@pytest.fixture(scope="session")
def rewards_app_spec(app_spec: ApplicationSpecification) -> ApplicationSpecification:
    """Get the application specification for the Rewards contract."""
    return app_spec


@pytest.fixture(scope="session")
def creator_account(algod_client: AlgodClient) -> Account:
    """Get the default account from the localnet."""
    return get_localnet_default_account(algod_client)


@pytest.fixture(scope="function")
def rewards_client(
    algod_client: AlgodClient,
    rewards_app_spec: ApplicationSpecification,
    creator_account: Account,
) -> ApplicationClient:
    """Create a new ApplicationClient for each test."""
    client = ApplicationClient(
        algod_client,
        app_spec=rewards_app_spec,
        signer=creator_account.signer,
        sender=creator_account.address,
    )
    client.create()
    return client


class TestRewardsIntegration:
    """Integration tests for the Rewards smart contract."""

    def test_setup_and_claim(
        self,
        rewards_client: ApplicationClient,
        creator_account: Account,
        algod_client: AlgodClient,
    ):
        """Test the full lifecycle: setup, add_allocations, and claim."""
        # Fund the app account
        rewards_client.fund(200_000)

        # Create a test asset
        sent_txn = algod_client.send_transaction(
            creator_account.signer.sign_transaction(
                TransactionWithSigner(
                    txn=AssetCreateTxn(
                        sender=creator_account.address,
                        sp=algod_client.suggested_params(),
                        total=1000,
                        decimals=0,
                        asset_name="TestCoin",
                        unit_name="TC",
                    ),
                    signer=creator_account.signer,
                )
            )
        )
        asset_id = algod_client.pending_transaction_info(sent_txn)["asset-index"]

        # Setup the contract
        rewards_client.call(
            "setup",
            token_id=asset_id,
            claim_period_duration=100,
            transaction_parameters={"foreign_assets": [asset_id]},
        )

        # Add an allocation
        user_account = Account()
        rewards_client.call(
            "add_allocations",
            addresses=[user_account.address],
            amounts=[100],
            boxes=[(rewards_client.app_id, user_account.address)],
        )

        # User claims the allocation
        user_client = rewards_client.prepare(signer=user_account.signer)
        user_client.call(
            "claim",
            boxes=[(rewards_client.app_id, user_account.address)],
        )

        # Verify user received the asset
        user_asset_info = algod_client.account_asset_info(
            user_account.address, asset_id
        )
        assert user_asset_info["asset-holding"]["amount"] == 100

    def test_claim_expired_fails(
        self,
        rewards_client: ApplicationClient,
        creator_account: Account,
        algod_client: AlgodClient,
    ):
        """Test that claiming an expired allocation fails."""
        rewards_client.fund(200_000)
        asset_id = 1  # Using a dummy asset ID for simplicity

        rewards_client.call(
            "setup",
            token_id=asset_id,
            claim_period_duration=1,  # 1 second
            transaction_parameters={"foreign_assets": [asset_id]},
        )

        user_account = Account()
        rewards_client.call(
            "add_allocations",
            addresses=[user_account.address],
            amounts=[100],
            boxes=[(rewards_client.app_id, user_account.address)],
        )

        # Wait for the claim period to expire
        import time

        time.sleep(2)

        user_client = rewards_client.prepare(signer=user_account.signer)
        with pytest.raises(Exception, match="Claim period has ended"):
            user_client.call(
                "claim",
                boxes=[(rewards_client.app_id, user_account.address)],
            )

    def test_reclaim_after_expiry(
        self,
        rewards_client: ApplicationClient,
        creator_account: Account,
        algod_client: AlgodClient,
    ):
        """Test that the admin can reclaim an allocation after it expires."""
        rewards_client.fund(200_000)
        asset_id = 1

        rewards_client.call(
            "setup",
            token_id=asset_id,
            claim_period_duration=1,
            transaction_parameters={"foreign_assets": [asset_id]},
        )

        user_account = Account()
        rewards_client.call(
            "add_allocations",
            addresses=[user_account.address],
            amounts=[100],
            boxes=[(rewards_client.app_id, user_account.address)],
        )

        time.sleep(2)

        rewards_client.call(
            "reclaim_allocation",
            user_address=user_account.address,
            boxes=[(rewards_client.app_id, user_account.address)],
        )

        # Verify the box has been deleted
        with pytest.raises(Exception, match="box not found"):
            algod_client.application_box_by_name(
                rewards_client.app_id, user_account.address.encode()
            )

    def test_non_admin_cannot_call_admin_methods(
        self, rewards_client: ApplicationClient
    ):
        """Test that non-admin users cannot call admin-only methods."""
        non_admin_account = Account()
        non_admin_client = rewards_client.prepare(signer=non_admin_account.signer)

        with pytest.raises(Exception, match="Sender is not the admin"):
            non_admin_client.call("setup", token_id=1, claim_period_duration=1)

        with pytest.raises(Exception, match="Sender is not the admin"):
            non_admin_client.call(
                "add_allocations", addresses=[Account().address], amounts=[100]
            )

        with pytest.raises(Exception, match="Sender is not the admin"):
            non_admin_client.call("reclaim_allocation", user_address=Account().address)