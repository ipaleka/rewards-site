from django.urls import path

from walletauth.views import WalletNonceView, WalletVerifyView


from django.http import JsonResponse


def check_auth(request):
    return JsonResponse({"is_authenticated": request.user.is_authenticated})


urlpatterns = [
    path("nonce/", WalletNonceView.as_view(), name="wallet_nonce"),
    path("verify/", WalletVerifyView.as_view(), name="wallet_verify"),
    path("check-auth/", check_auth, name="check_auth"),
]
