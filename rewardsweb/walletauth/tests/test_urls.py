"""Testing module for walletauth app's URL dispatcher module."""

from django.urls import URLPattern

from walletauth import urls


class TestWalletauthUrls:
    """Testing class for :py:mod:`walletauth.urls` module."""

    def _url_from_pattern(self, pattern):
        return next(url for url in urls.urlpatterns if str(url.pattern) == pattern)

    def test_walletauth_urls_nonce(self):
        url = self._url_from_pattern("nonce/")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "walletauth.views.WalletNonceView"
        assert url.name == "wallet_nonce"

    def test_walletauth_urls_verify(self):
        url = self._url_from_pattern("verify/")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "walletauth.views.WalletVerifyView"
        assert url.name == "wallet_verify"

    def test_walletauth_urls_patterns_count(self):
        assert len(urls.urlpatterns) == 2
