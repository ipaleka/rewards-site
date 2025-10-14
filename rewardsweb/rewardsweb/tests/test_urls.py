"""Testing module for website's synchronous url dispatcher module."""

from django.urls import URLResolver

from rewardsweb import urls


class TestRewardsWebUrls:
    """Testing class for :py:mod:`rewardsweb.urls` module."""

    def _url_from_pattern(self, pattern):
        return next(url for url in urls.urlpatterns if str(url.pattern) == pattern)

    def test_rewardsweb_urls_api(self):
        url = self._url_from_pattern("api/")
        assert isinstance(url, URLResolver)
        assert "api.urls" in str(url.urlconf_name)

    def test_rewardsweb_urls_core_app(self):
        url = self._url_from_pattern("")
        assert isinstance(url, URLResolver)
        assert "core.urls" in str(url.urlconf_name)

    def test_rewardsweb_urls_pattern_count(self):
        assert len(urls.urlpatterns) == 5
