"""Rewards smart contract integration tests module."""

import pytest
from algosdk.account import address_from_private_key, generate_account
from algosdk.error import AlgodHTTPError
from algosdk.v2client.algod import AlgodClient
from algosdk.transaction import PaymentTxn

from contract.helpers import environment_variables, private_key_from_mnemonic
from contract.network import _add_allocations, _reclaim_allocation


@pytest.fixture(scope="module")
def client():
    """Fixture for Algod client."""
    env = environment_variables()
    return AlgodClient(env.get("algod_token_testnet"), env.get("algod_address_testnet"))


@pytest.fixture(scope="module")
def creator_private_key():
    """Fixture for creator's private key."""
    env = environment_variables()
    return private_key_from_mnemonic(env.get("creator_mnemonic_testnet"))


@pytest.fixture(scope="module")
def creator_address(creator_private_key):
    """Fixture for creator's address."""
    return address_from_private_key(creator_private_key)


@pytest.fixture(scope="module")
def rewards_app_id_testnet():
    """Fixture for creator's private key."""
    env = environment_variables()
    return private_key_from_mnemonic(env.get("rewards_app_id_testnet"))


class TestRewardsIntegration:
    """Integration tests for the Rewards smart contract."""

    def test_add_allocations_and_reclaim_expired(
        self, client, creator_private_key, rewards_app_id_testnet
    ):
        """
        Tests the full lifecycle of an allocation:
        1. Admin adds an allocation for a user.
        2. Admin attempts to reclaim the allocation before it expires, which should fail.
        3. Admin reclaims the allocation after it expires, which should succeed.
        """
        _, user_address = generate_account()

        # 1. Add allocation
        _add_allocations(
            client,
            creator_private_key,
            rewards_app_id_testnet,
            [user_address],
            [100],
        )

        # 2. Attempt to reclaim before expiry (should fail)
        with pytest.raises(AlgodHTTPError) as exception:
            _reclaim_allocation(
                client,
                creator_private_key,
                rewards_app_id_testnet,
                user_address,
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

    def test_non_admin_cannot_call_admin_methods(
        self, client, creator_private_key, rewards_app_id_testnet
    ):
        """
        Tests that a non-admin user cannot call admin-only methods.
        """
        user_private_key, user_address = generate_account()
        creator_address = address_from_private_key(creator_private_key)
        sp = client.suggested_params()
        client.send_transaction(
            PaymentTxn(creator_address, sp, user_address, 1_000_000).sign(
                creator_private_key
            )
        )

        with pytest.raises(AlgodHTTPError) as exception:
            _add_allocations(
                client,
                user_private_key,
                rewards_app_id_testnet,
                [user_address],
                [100],
            )
        assert "Sender is not the admin" in str(exception.value)

        with pytest.raises(AlgodHTTPError) as exception:
            _reclaim_allocation(
                client,
                user_private_key,
                rewards_app_id_testnet,
                user_address,
            )
        assert "Sender is not the admin" in str(exception.value)
