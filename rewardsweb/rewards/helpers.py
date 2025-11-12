"""Module containing rewards app helper functions."""

from django.contrib import messages

from core.models import Contribution, IssueStatus


def added_allocations_for_addresses(request, addresses, txid):
    """Process successful allocation transactions and update issue statuses.

    This function handles the successful completion of allocation transactions by:
    - Displaying a success message with the transaction ID
    - Updating the status of addressed issues for the given addresses
    - Logging the allocation action in the user's profile

    Args:
        request: The HTTP request object containing user and session data
        addresses (list): List of wallet addresses that received allocations
        txid (str): Transaction ID of the successful allocation transaction

    Note:
        If txid is None or empty, the function returns without performing any actions.
    """
    if txid:
        messages.success(request, f"✅ Allocation successful TXID: {txid}")
        contributions = Contribution.objects.filter(issue__status=IssueStatus.ADDRESSED)
        Contribution.objects.update_issue_statuses_for_addresses(
            addresses, contributions
        )
        request.user.profile.log_action(
            "boxes_created",
            txid
            + "; "
            + "; ".join([addr[:5] + ".." + addr[-5:] for addr in addresses]),
        )


def reclaimed_allocation_for_address(request, address, txid):
    """Process successful allocation reclamation and log the action.

    This function handles the successful reclamation of an allocation by:
    - Displaying a success message with the address and transaction ID
    - Logging the reclamation action in the user's profile

    Args:
        request: The HTTP request object containing user and session data
        address (str): Wallet address from which the allocation was reclaimed
        txid (str): Transaction ID of the successful reclamation transaction

    Note:
        If txid is None or empty, the function returns without performing any actions.
    """
    if txid:
        messages.success(request, f"✅ Successfully reclaimed {address} (TXID: {txid})")
        request.user.profile.log_action("allocation_reclaimed", address)
