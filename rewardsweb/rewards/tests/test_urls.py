"""Testing module for rewards app's URL dispatcher module."""

from django.urls import URLPattern

from rewards import urls


class TestRewardsUrls:
    """Testing class for :py:mod:`rewards.urls` module."""

    def _url_from_pattern(self, pattern):
        return next(url for url in urls.urlpatterns if str(url.pattern) == pattern)
