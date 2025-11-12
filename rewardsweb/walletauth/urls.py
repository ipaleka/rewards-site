"""Module containing walletauth app's URL configuration."""

from django.urls import path

from walletauth.views import (
    ActiveNetworkAPIView,
    AddAllocationsAPIView,
    AllocationsSuccessfulAPIView,
    ClaimAllocationAPIView,
    ReclaimAllocationsAPIView,
    UserClaimedAPIView,
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
    path("add-allocations/", AddAllocationsAPIView.as_view(), name="add_allocations"),
    path(
        "allocations-successful/",
        AllocationsSuccessfulAPIView.as_view(),
        name="allocations_successful",
    ),
    path(
        "claim-allocation/", ClaimAllocationAPIView.as_view(), name="claim_allocation"
    ),
    path("user-claimed/", UserClaimedAPIView.as_view(), name="user_claimed"),
    path(
        "reclaim-allocations/",
        ReclaimAllocationsAPIView.as_view(),
        name="reclaim_allocations",
    ),
]
