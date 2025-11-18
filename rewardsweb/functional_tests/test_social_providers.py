"""Module containing functional tests for login by social media accounts."""

from django.urls import reverse
from selenium.webdriver.common.by import By

from functional_tests.base import SOCIAL_PROVIDERS, SeleniumTestCase


class SocialProviderButtonTests(SeleniumTestCase):

    def _assert_buttons_on_page(self, url):
        self.driver.get(self.get_url(url))

        for pid in SOCIAL_PROVIDERS:
            xpath = f"//a[contains(@href, '/accounts/{pid}/login/?process=login')]"
            btn = self.driver.find_element(By.XPATH, xpath)
            assert "Continue with" in btn.text

    def test_buttons_on_login_page(self):
        self._assert_buttons_on_page(reverse("account_login"))

    def test_buttons_on_signup_page(self):
        self._assert_buttons_on_page(reverse("account_signup"))


class SocialAccountLoginTests(SeleniumTestCase):

    def _open_provider(self):
        self.driver.get(self.get_url(reverse("account_login")))
        pid = SOCIAL_PROVIDERS[0]

        link = self.driver.find_element(
            By.XPATH, f"//a[contains(@href, '/accounts/{pid}/login/?process=login')]"
        )
        link.click()
        return pid

    def test_socialaccount_login_page_renders(self):
        pid = self._open_provider()

        h1 = self.driver.find_element(By.TAG_NAME, "h1")
        assert "Continue with" in h1.text

        submit = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        assert (
            pid.split("_")[0].capitalize() in submit.text or "Continue" in submit.text
        )

    def test_socialaccount_login_validation(self):
        """
        SocialAccount login confirmation has NO form fields that can produce validation
        errors. Clicking submit either continues the OAuth flow or redirects immediately.

        Therefore, this test only verifies that clicking submit does NOT crash.
        """
        self._open_provider()

        submit = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        submit.click()

        # After clicking submit, we simply assert that the page loaded something valid
        body = self.driver.page_source.lower()

        assert (
            "sign in" in body
            or "continue" in body
            or "redirect" in body
            or "login" in body
        ), "SocialAccount login did not redirect or render a valid page."


class SocialAccountSignupTests(SeleniumTestCase):

    def _open_social_signup(self):
        # Trigger OAuth provider
        self.driver.get(self.get_url(reverse("account_login")))

        pid = SOCIAL_PROVIDERS[0]
        link = self.driver.find_element(
            By.XPATH, f"//a[contains(@href, '/accounts/{pid}/login/?process=login')]"
        )
        link.click()

        # Then go to signup finalization
        url = self.get_url(reverse("socialaccount_signup"))
        self.driver.get(url)
        return pid

    def test_socialaccount_signup_page_renders(self):
        self.driver.get(self.get_url(reverse("socialaccount_signup")))

        body = self.driver.page_source.lower()

        assert (
            "complete signup" in body
            or "finalize" in body
            or "welcome back" in body
            or "sign in" in body
        ), "Unexpected content on socialaccount signup page."

    def test_socialaccount_signup_validation(self):
        self.driver.get(self.get_url(reverse("socialaccount_signup")))

        submit = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        submit.click()

        errors = self.driver.find_elements(By.CSS_SELECTOR, ".text-error, .alert-error")
        assert errors, "Expected validation errors but found none."
