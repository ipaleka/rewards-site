import pytest
from django.http import Http404
from django.template.loader import render_to_string
from django.urls import reverse


@pytest.mark.django_db
class TestIssueModalHTMX:
    """Tests loading modal fragments dynamically via HTMX."""

    def test_issuemodalview_htmx_modal_loads(self, client, superuser, issue):
        """Modal fragment loads correctly using HTMX."""
        client.force_login(superuser)

        url = reverse("issue-modal", kwargs={"pk": issue.pk}) + "?action=addressed"
        response = client.get(url, HTTP_HX_REQUEST="true")

        assert response.status_code == 200
        content = response.content.decode()

        assert "<dialog" in content
        assert f"close-addressed-modal" in content

    def test_modal_raises_404_for_non_superuser(self, client, issue):
        """Anonymous or normal user should trigger Http404"""
        url = reverse("issue-modal", kwargs={"pk": issue.pk}) + "?action=addressed"
        response = client.get(url, HTTP_HX_REQUEST="true")
        assert response.status_code == 404

    def test_modal_raises_404_for_invalid_action(self, client, superuser, issue):
        """Invalid ?action should raise Http404"""
        client.force_login(superuser)

        url = reverse("issue-modal", kwargs={"pk": issue.pk}) + "?action=banana"
        response = client.get(url, HTTP_HX_REQUEST="true")
        assert response.status_code == 404

    def test_issue_detail_view_handle_labels_submission_htmx(
        self, client, superuser, issue, mocker
    ):
        """IssueDetailView._handle_labels_submission should return HTMX partial on success."""
        client.force_login(superuser)

        mocked_set_labels = mocker.patch(
            "core.views.set_labels_to_issue",
            return_value={
                "success": True,
                "message": f"some message",
                "current_labels": ["bug", "high priority"],
            },
        )
        url = reverse("issue-detail", kwargs={"pk": issue.pk})
        data = {
            "submit_labels": "",
            "labels": ["bug"],
            "priority": "high priority",
        }
        response = client.post(url, data, HTTP_HX_REQUEST="true")

        assert response.status_code == 200
        content = response.content.decode()

        assert "<form" in content
        assert "bug" in content
        assert "high priority" in content
        assert "Labels updated successfully" in content
