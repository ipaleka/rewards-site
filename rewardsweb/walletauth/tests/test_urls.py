"""Testing module for walletauth app's URL dispatcher module."""

from django.urls import URLPattern

from walletauth import urls


class TestWalletauthUrls:
    """Testing class for :py:mod:`walletauth.urls` module."""

    def _url_from_pattern(self, pattern):
        return next(url for url in urls.urlpatterns if str(url.pattern) == pattern)

    def test_walletauth_urls_wallets(self):
        url = self._url_from_pattern("wallets/")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "walletauth.views.WalletsAPIView"
        assert url.name == "wallets_api"

    def test_walletauth_urls_active_network(self):
        url = self._url_from_pattern("active-network/")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "walletauth.views.ActiveNetworkAPIView"
        assert url.name == "active_network_api"

    def test_walletauth_urls_nonce(self):
        url = self._url_from_pattern("nonce/")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "walletauth.views.WalletNonceAPIView"
        assert url.name == "wallet_nonce"

    def test_walletauth_urls_verify(self):
        url = self._url_from_pattern("verify/")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "walletauth.views.WalletVerifyAPIView"
        assert url.name == "wallet_verify"

    def test_walletauth_urls_claim_allocation(self):
        url = self._url_from_pattern("claim-allocation/")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "walletauth.views.ClaimAllocationAPIView"
        assert url.name == "claim_allocation"

    def test_walletauth_urls_add_allocations(self):
        url = self._url_from_pattern("add-allocations/")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "walletauth.views.AddAllocationsAPIView"
        assert url.name == "add_allocations"

    def test_walletauth_urls_allocations_successful(self):
        url = self._url_from_pattern("allocations-successful/")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "walletauth.views.AllocationsSuccessfulAPIView"
        assert url.name == "allocations_successful"

    def test_walletauth_urls_claim_successful(self):
        url = self._url_from_pattern("claim-successful/")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "walletauth.views.ClaimSuccessfulAPIView"
        assert url.name == "claim_successful"

    def test_walletauth_urls_reclaim_allocations(self):
        url = self._url_from_pattern("reclaim-allocations/")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "walletauth.views.ReclaimAllocationsAPIView"
        assert url.name == "reclaim_allocations"

    def test_walletauth_urls_reclaim_successful(self):
        url = self._url_from_pattern("reclaim-successful/")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "walletauth.views.ReclaimSuccessfulAPIView"
        assert url.name == "reclaim_successful"

    def test_walletauth_urls_patterns_count(self):
        assert len(urls.urlpatterns) == 10
