"""Module containing rewards app helper functions."""

from django.contrib import messages

from core.models import Contribution, IssueStatus


def added_allocations_for_addresses(request, addresses, txid):
    """TODO: docstring and tests"""
    if txid:
        messages.success(request, f"✅ Allocation successful TXID: {txid}")
        contributions = Contribution.objects.filter(issue__status=IssueStatus.ADDRESSED)
        Contribution.objects.update_issue_statuses_for_addresses(
            addresses, contributions
        )
        request.user.profile.log_action(
            "boxes_created",
            f"{txid}; ".join([addr[:5] + ".." + addr[-5:] for addr in addresses]),
        )



def reclaimed_allocation_for_address(request, address, txid):
    """TODO: docstring and tests"""
    if txid:
        messages.success(
            request, f"✅ Successfully reclaimed {address} (TXID: {txid})"
        )
        request.user.profile.log_action("allocation_reclaimed", address)
