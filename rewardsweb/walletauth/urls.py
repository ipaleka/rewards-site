"""Module containing walletauth app's URL configuration."""

from django.urls import path

from walletauth.views import (
    AddAllocationsView,
    ClaimAllocationView,
    ReclaimAllocationsView,
    WalletNonceView,
    WalletVerifyView,
)

urlpatterns = [
    path("nonce/", WalletNonceView.as_view(), name="wallet_nonce"),
    path("verify/", WalletVerifyView.as_view(), name="wallet_verify"),
    path("claim-allocation/", ClaimAllocationView.as_view(), name="claim_allocation"),
    path("add-allocations/", AddAllocationsView.as_view(), name="add_allocations"),
    path(
        "reclaim-allocations/",
        ReclaimAllocationsView.as_view(),
        name="reclaim_allocations",
    ),
]
