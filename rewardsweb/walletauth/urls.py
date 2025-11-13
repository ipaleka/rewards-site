"""Module containing walletauth app's URL configuration."""

from django.urls import path

from walletauth.views import (
    ActiveNetworkAPIView,
    AddAllocationsAPIView,
    AllocationsSuccessfulAPIView,
    ClaimAllocationAPIView,
    ReclaimAllocationsAPIView,
    ReclaimSuccessfulAPIView,
    ClaimSuccessfulAPIView,
    WalletNonceAPIView,
    WalletsAPIView,
    WalletVerifyAPIView,
)

urlpatterns = [
    path("wallets/", WalletsAPIView.as_view(), name="wallets_api"),
    path(
        "active-network/",
        ActiveNetworkAPIView.as_view(),
        name="active_network_api",
    ),
    path("nonce/", WalletNonceAPIView.as_view(), name="wallet_nonce"),
    path("verify/", WalletVerifyAPIView.as_view(), name="wallet_verify"),
    path("add-allocations/", AddAllocationsAPIView.as_view(), name="auth_add_allocations"),
    path(
        "allocations-successful/",
        AllocationsSuccessfulAPIView.as_view(),
        name="allocations_successful",
    ),
    path(
        "claim-allocation/", ClaimAllocationAPIView.as_view(), name="auth_claim_allocation"
    ),
    path("claim-successful/", ClaimSuccessfulAPIView.as_view(), name="claim_successful"),
    path(
        "reclaim-allocations/",
        ReclaimAllocationsAPIView.as_view(),
        name="auth_reclaim_allocations",
    ),
    path(
        "reclaim-successful/",
        ReclaimSuccessfulAPIView.as_view(),
        name="reclaim_successful",
    ),
]
