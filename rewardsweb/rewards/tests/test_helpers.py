"""Testing module for rewards app helper functions."""

import pytest

from core.models import IssueStatus
from rewards.helpers import (
    added_allocations_for_addresses,
    reclaimed_allocation_for_address,
)


class TestRewardsHelpers:
    """Testing class for :py:mod:`rewards.helpers`"""

    # # added_allocations_for_addresses
    def test_rewards_helpers_added_allocations_for_addresses_for_no_txid(self, mocker):
        request = mocker.MagicMock()
        addresses = "ADDR1AAAAADDR1", "ADDR2AAAAADDR2"
        txid = None
        mocked_success = mocker.patch("rewards.helpers.messages.success")
        mocked_filter = mocker.patch("rewards.helpers.Contribution.objects.filter")
        mocked_update = mocker.patch(
            "rewards.helpers.Contribution.objects.update_issue_statuses_for_addresses"
        )
        added_allocations_for_addresses(request, addresses, txid)
        mocked_success.assert_not_called()
        mocked_filter.assert_not_called()
        mocked_update.assert_not_called()
        request.user.profile.log_action.assert_not_called()

    def test_rewards_helpers_added_allocations_for_addresses_functionality(
        self, mocker
    ):
        request = mocker.MagicMock()
        addresses = "ADDR1AAAAADDR1", "ADDR2AAAAADDR2"
        txid = "txid"
        mocked_success = mocker.patch("rewards.helpers.messages.success")
        contributions = mocker.MagicMock()
        mocked_filter = mocker.patch(
            "rewards.helpers.Contribution.objects.filter",
            return_value=contributions,
        )
        mocked_update = mocker.patch(
            "rewards.helpers.Contribution.objects.update_issue_statuses_for_addresses"
        )
        added_allocations_for_addresses(request, addresses, txid)
        mocked_success.assert_called_once_with(
            request, f"✅ Allocation successful TXID: {txid}"
        )
        mocked_filter.assert_called_once_with(issue__status=IssueStatus.ADDRESSED)
        mocked_update.assert_called_once_with(addresses, contributions)
        request.user.profile.log_action.assert_called_once_with(
            "boxes_created",
            txid
            + "; "
            + "; ".join([addr[:5] + ".." + addr[-5:] for addr in addresses]),
        )

    # # reclaimed_allocation_for_address
    def test_rewards_helpers_reclaimed_allocation_for_address_for_no_txid(self, mocker):
        request = mocker.MagicMock()
        address = "ADDR1AAAAADDR1"
        txid = None
        mocked_success = mocker.patch("rewards.helpers.messages.success")
        reclaimed_allocation_for_address(request, address, txid)
        mocked_success.assert_not_called()
        request.user.profile.log_action.assert_not_called()

    def test_rewards_helpers_reclaimed_allocation_for_address_functionality(
        self, mocker
    ):
        request = mocker.MagicMock()
        address = "ADDR1AAAAADDR1"
        txid = "txid"
        mocked_success = mocker.patch("rewards.helpers.messages.success")
        reclaimed_allocation_for_address(request, address, txid)
        mocked_success.assert_called_once_with(
            request, f"✅ Successfully reclaimed {address} (TXID: {txid})"
        )
        request.user.profile.log_action.assert_called_once_with(
            "allocation_reclaimed", address
        )
