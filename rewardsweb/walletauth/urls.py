from django.urls import path

from walletauth.views import WalletNonceView, WalletVerifyView

urlpatterns = [
    path("nonce/", WalletNonceView.as_view(), name="wallet_nonce"),
    path("verify/", WalletVerifyView.as_view(), name="wallet_verify"),
]
