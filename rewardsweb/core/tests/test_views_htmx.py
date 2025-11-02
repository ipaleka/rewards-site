import pytest
from django.urls import reverse
from django.http import Http404


@pytest.mark.django_db
class TestIssueDetailHTMX:
    """Tests verifying HTMX fragment responses on label submission."""

    def test_issuedetailview_htmx_labels_submit_success(
        self, client, superuser, issue, mocker
    ):
        """HTMX POST returns HTML fragment instead of redirect."""
        mock_add_labels = mocker.patch("core.views.set_labels_to_issue")
        mock_add_labels.return_value = {"success": True}

        client.force_login(superuser)

        url = reverse("issue-detail", kwargs={"pk": issue.pk})
        response = client.post(
            url,
            {
                "labels": ["bug"],
                "priority": "high priority",
                "submit_labels": "Set labels",
            },
            HTTP_HX_REQUEST="true",  # 🚀 simulate HTMX
        )

        assert response.status_code == 200
        content = response.content.decode()

        # Fragment should contain form, not entire layout
        assert "<form" in content
        assert "</html>" not in content

        # Toast message should appear in data attributes
        assert "data-toast-message" in content

        # Backend must call API
        mock_add_labels.assert_called_once_with(
            superuser, issue.number, ["bug", "high priority"]
        )

    def test_issuedetailview_htmx_labels_submit_form_error(
        self, client, superuser, issue
    ):
        """Invalid label submission returns same partial with errors."""
        client.force_login(superuser)

        url = reverse("issue-detail", kwargs={"pk": issue.pk})

        response = client.post(
            url,
            {
                "priority": "medium priority",
                "submit_labels": "Set labels",
            },
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == 200
        content = response.content.decode()

        assert "<form" in content
        assert "Please correct the errors" in content
        assert "</html>" not in content
        
    def test_non_htmx_still_redirects(self, client, superuser, issue, mocker):
        mock_add_labels = mocker.patch("core.views.set_labels_to_issue")
        mock_add_labels.return_value = {"success": True}

        client.force_login(superuser)
        url = reverse("issue-detail", kwargs={"pk": issue.pk})

        response = client.post(
            url,
            {"labels": ["bug"], "priority": "medium priority", "submit_labels": "Set labels"},
        )

        assert response.status_code == 302  # ✅ redirect for non-HTMX


@pytest.mark.django_db
class TestIssueModalHTMX:
    """Tests loading modal fragments dynamically via HTMX."""

    def test_issuemodalview_htmx_modal_loads(self, client, superuser, issue):
        """Modal fragment loads correctly using HTMX."""
        client.force_login(superuser)

        url = reverse("issue-modal", kwargs={"pk": issue.pk}) + "?action=addressed"
        response = client.get(url, HTTP_HX_REQUEST="true")  # ✅ simulate HTMX GET

        assert response.status_code == 200
        content = response.content.decode()

        assert "<dialog" in content
        assert f"close-addressed-modal" in content

    def test_issuemodalview_htmx_modal_requires_valid_action(
        self, client, superuser, issue
    ):
        client.force_login(superuser)

        url = reverse("issue-modal", kwargs={"pk": issue.pk}) + "?action=invalid"

        with pytest.raises(Http404):
            client.get(url, HTTP_HX_REQUEST="true")
