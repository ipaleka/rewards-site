"""Module containing functional tests for the website's index page."""

from django.contrib.auth import get_user_model
from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from functional_tests.base import SeleniumTestCase

User = get_user_model()


class LoginFormTests(SeleniumTestCase):

    def setUp(self):
        super().setUp()
        self.password = "secret123"
        self.user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password=self.password,
        )

    def test_login_via_form(self):
        login_url = self.get_url(reverse("account_login"))
        index_url = self.get_url(reverse("index"))

        self.driver.get(login_url)

        self.driver.find_element(By.NAME, "login").send_keys(self.user.username)
        self.driver.find_element(By.NAME, "password").send_keys(self.password)

        submit = self.driver.find_element(
            By.XPATH, "//form[@method='post']//button[@type='submit']"
        )
        submit.click()

        self.driver.implicitly_wait(2)
        self.assertTrue(self.driver.current_url.startswith(index_url))

        badge = self.driver.find_element(
            By.XPATH, f"//span[contains(., '{self.user.username}')]"
        )
        self.assertTrue(badge.is_displayed())


class SidebarTests(SeleniumTestCase):

    def test_sidebar_highlights_current_page(self):
        url = self.get_url(reverse("index"))
        self.driver.get(url)

        index_url = self.get_url(reverse("index"))

        links = self.driver.find_elements(
            By.XPATH, "//div[contains(@class,'drawer-side')]//a[@href]"
        )

        active = [
            link for link in links if link.get_attribute("href").startswith(index_url)
        ]

        self.assertGreaterEqual(len(active), 1)


class ThemeSwitcherTests(SeleniumTestCase):

    def test_theme_switch_persists(self):
        url = self.get_url(reverse("index"))
        self.driver.get(url)

        # open dropdown
        palette_button = self.driver.find_element(
            By.XPATH,
            "//i[contains(@class, 'fa-palette')]/ancestor::div[@role='button']",
        )
        palette_button.click()

        dark = self.driver.find_element(
            By.XPATH, "//input[@name='theme-dropdown' and @value='dark']"
        )
        dark.click()

        theme = self.driver.execute_script(
            "return document.documentElement.getAttribute('data-theme')"
        )
        self.assertEqual(theme, "dark")

        self.driver.refresh()

        theme_after = self.driver.execute_script(
            "return document.documentElement.getAttribute('data-theme')"
        )
        self.assertEqual(theme_after, "dark")


class SidebarNavigationTests(SeleniumTestCase):

    def test_sidebar_has_main_navigation_section(self):
        self.driver.get(self.get_url(reverse("index")))
        self.wait_for_sidebar()

        # Ensure the Main Navigation header exists
        title = self.driver.find_element(
            By.XPATH,
            "//li[contains(@class,'menu-title') and normalize-space()='Main Navigation']",
        )
        self.assertIsNotNone(title, "Main Navigation section should exist in sidebar.")

    def test_sidebar_contains_expected_links(self):
        self.driver.get(self.get_url(reverse("index")))
        self.wait_for_sidebar()

        expected_links = {
            "Home": reverse("index"),
            "Contributors": reverse("contributors"),
            "Cycles": reverse("cycles"),
            "Issues": reverse("issues"),
        }

        sidebar = self.driver.find_element(
            By.XPATH, "//div[contains(@class,'drawer-side')]"
        )

        for link_text, url in expected_links.items():
            xpath = f".//a[contains(@href, '{url}') and contains(., '{link_text}')]"

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )

            elem = sidebar.find_element(By.XPATH, xpath)
            self.assertIsNotNone(
                elem, f"Sidebar should contain link '{link_text}' → {url}"
            )

    def test_sidebar_highlights_home_as_active_on_index(self):
        """The Home link should have the 'active' class when visiting /index."""
        self.driver.get(self.get_url(reverse("index")))
        self.wait_for_sidebar()

        home_url = reverse("index")

        active_home = self.driver.find_element(
            By.XPATH,
            f"//a[contains(@href, '{home_url}') and contains(@class, 'active')]",
        )

        self.assertIsNotNone(
            active_home, "Home link should have 'active' class when on index page."
        )
