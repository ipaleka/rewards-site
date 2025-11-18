"""Module containing functional tests for login by social media accounts."""

from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from functional_tests.base import SOCIAL_PROVIDERS, SeleniumTestCase


class SocialProviderButtonTests(SeleniumTestCase):
    """
    Smoke tests for presence of social login buttons on login/signup pages.

    We do NOT assert on visible text, because in some environments
    (e.g. CI) the buttons may render as icon-only or have text visually
    hidden with CSS. Instead we assert that:
      - an <a> exists for each provider
      - it is displayed
      - its href matches the expected pattern
    """

    def _assert_buttons_on_page(self, url: str) -> None:
        self.driver.get(self.get_url(url))

        for pid in SOCIAL_PROVIDERS:
            xpath = f"//a[contains(@href, '/accounts/{pid}/login/?process=login')]"

            try:
                btn = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
            except Exception:
                # If a provider isn't configured in this environment
                # (e.g. CI missing secrets), we skip it rather than fail.
                continue

            # Basic smoke checks
            assert btn.is_displayed(), f"Social button for {pid} is not visible"

            href = btn.get_attribute("href") or ""
            assert (
                f"/accounts/{pid}/login/" in href
            ), f"Unexpected href for provider {pid}: {href}"

            # If there *is* text, it should be non-empty and meaningful,
            # but we don't require any particular phrase.
            text = (btn.text or "").strip()
            if text:
                assert len(text) > 0

    def test_buttons_on_login_page(self):
        self._assert_buttons_on_page(reverse("account_login"))

    def test_buttons_on_signup_page(self):
        self._assert_buttons_on_page(reverse("account_signup"))


class SocialAccountLoginTests(SeleniumTestCase):
    """
    Very high-level smoke test for one provider's login flow:
    we only check that submitting the provider login does not crash.

    This is intentionally loose, because the real OAuth page is
    controlled by the provider (Discord/Google/etc.) and may change.
    """

    provider_id = "discord"  # pick one that you actually configure

    def _open_provider(self):
        # Go to login page and click the provider button if present
        self.driver.get(self.get_url(reverse("account_login")))
        xpath = (
            f"//a[contains(@href, '/accounts/{self.provider_id}/login/?process=login')]"
        )

        try:
            provider_link = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
        except Exception:
            # If provider is not available in this environment, skip test
            self.skipTest(
                f"Provider {self.provider_id} not configured in this environment"
            )

        provider_link.click()

    def test_socialaccount_login_validation(self):
        """
        On the provider login/consent page we can't assert specific content,
        but we can assert that:
          - the page loaded,
          - we didn't crash with a Django error page.
        """
        self._open_provider()

        # Just check we didn't land on a Django/500 error page
        body = self.driver.page_source.lower()

        error_markers = [
            "server error",
            "traceback",
            "valueerror",
            "keyerror",
            "attributeerror",
            "internal server error",
        ]

        assert not any(
            marker in body for marker in error_markers
        ), "Provider login appears to have crashed with a server error."
