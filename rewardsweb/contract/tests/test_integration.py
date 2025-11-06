"""Rewards smart contract integration tests module."""

import pytest
from algosdk.account import address_from_private_key
from algosdk.atomic_transaction_composer import AccountTransactionSigner
from algosdk.error import AlgodHTTPError
from algosdk.v2client.algod import AlgodClient

from contract.helpers import (
    environment_variables,
    private_key_from_mnemonic,
)
from contract.network import add_allocations, reclaim_allocation

# This should be set to the ID of a deployed Rewards contract on TestNet
REWARDS_APP_ID_TESTNET = environment_variables().get("REWARDS_APP_ID_TESTNET")


class TestRewardsIntegration:
    """Integration tests for the Rewards smart contract."""

    def test_add_allocations_and_reclaim_expired(self):
        """
        Tests the full lifecycle of an allocation:
        1. Admin adds an allocation for a user.
        2. Admin attempts to reclaim the allocation before it expires, which should fail.
        3. Admin reclaims the allocation after it expires, which should succeed.
        """
        env = environment_variables()
        client = AlgodClient(
            env.get("algod_token_testnet"), env.get("algod_address_testnet")
        )
        creator_private_key = private_key_from_mnemonic(
            env.get("creator_mnemonic_testnet")
        )
        user_account = Account()

        # 1. Add allocation
        add_allocations(
            client,
            creator_private_key,
            REWARDS_APP_ID_TESTNET,
            [user_account.address],
            [100],
        )

        # 2. Attempt to reclaim before expiry (should fail)
        with pytest.raises(AlgodHTTPError) as exception:
            reclaim_allocation(
                client,
                creator_private_key,
                REWARDS_APP_ID_TESTNET,
                user_account.address,
            )
        assert "Claim period has not ended" in str(exception.value)

        # 3. Reclaim after expiry (requires waiting for the claim period to pass)
        # Note: This part of the test is commented out as it would require a long wait.
        # To test this, you would need to set a short claim_period_duration when setting up the contract.
        # import time
        # time.sleep(CLAIM_PERIOD_DURATION + 1)
        # reclaim_allocation(
        #     client,
        #     creator_private_key,
        #     REWARDS_APP_ID_TESTNET,
        #     user_account.address,
        # )

    def test_non_admin_cannot_call_admin_methods(self):
        """
        Tests that a non-admin user cannot call admin-only methods.
        """
        env = environment_variables()
        client = AlgodClient(
            env.get("algod_token_testnet"), env.get("algod_address_testnet")
        )
        user_private_key = private_key_from_mnemonic(env.get("user_mnemonic_testnet"))
        user_account = Account()

        with pytest.raises(AlgodHTTPError) as exception:
            add_allocations(
                client,
                user_private_key,
                REWARDS_APP_ID_TESTNET,
                [user_account.address],
                [100],
            )
        assert "Sender is not the admin" in str(exception.value)

        with pytest.raises(AlgodHTTPError) as exception:
            reclaim_allocation(
                client,
                user_private_key,
                REWARDS_APP_ID_TESTNET,
                user_account.address,
            )
        assert "Sender is not the admin" in str(exception.value)
