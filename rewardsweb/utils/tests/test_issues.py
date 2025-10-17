"""Testing module for :py:mod:`utils.issues` module."""

from django.conf import settings

from utils.issues import _github_client, _github_repository, create_github_issue


class TestUtilsIssuesFunctions:
    """Testing class for :py:mod:`utils.issues` functions."""

    # # _github_client
    def test_utils_issues_github_client_for_no_token(self, mocker):
        user = mocker.MagicMock()
        user.profile.github_access_token = None
        mocked_auth = mocker.patch("utils.issues.Auth.Token")
        returned = _github_client(user)
        assert returned is False
        mocked_auth.assert_not_called()

    def test_utils_issues_github_client_functionality(self, mocker):
        user = mocker.MagicMock()
        token = mocker.MagicMock()
        auth, client = mocker.MagicMock(), mocker.MagicMock()
        mocked_auth = mocker.patch("utils.issues.Auth.Token", return_value=auth)
        mocked_client = mocker.patch("utils.issues.Github", return_value=client)
        user.profile.github_access_token = token
        returned = _github_client(user)
        assert returned == client
        mocked_auth.assert_called_once_with(token)
        mocked_client.assert_called_once_with(auth=auth)

    # # _github_repository
    def test_utils_issues_github_repository_functionality(self, mocker):
        client = mocker.MagicMock()
        returned = _github_repository(client)
        assert returned == client.get_repo.return_value
        client.get_repo.assert_called_once_with(
            f"{settings.GITHUB_REPO_OWNER}/{settings.GITHUB_REPO_NAME}"
        )

    # # create_github_issue
    def test_utils_issues_create_github_issue_for_no_client(self, mocker):
        user = mocker.MagicMock()
        mocked_client = mocker.patch("utils.issues._github_client", return_value=False)
        mocked_repo = mocker.patch("utils.issues._github_repository")
        returned = create_github_issue(user, mocker.MagicMock(), mocker.MagicMock())
        assert returned == {
            "success": False,
            "error": "Please provide a GitHub access token in your profile page!",
        }
        mocked_client.assert_called_once_with(user)
        mocked_repo.assert_not_called()

    def test_utils_issues_create_github_issue_for_error_during_creation(self, mocker):
        user = mocker.MagicMock()
        title, body = "title", "body text"
        client, repo = mocker.MagicMock(), mocker.MagicMock()
        mocked_client = mocker.patch("utils.issues._github_client", return_value=client)
        mocked_repo = mocker.patch("utils.issues._github_repository", return_value=repo)
        repo.create_issue.side_effect = Exception("Create error")
        returned = create_github_issue(user, title, body)
        assert returned == {"success": False, "error": "Create error"}
        mocked_client.assert_called_once_with(user)
        mocked_repo.assert_called_once_with(client)
        repo.create_issue.assert_called_once_with(title=title, body=body, labels=[])
        client.close.assert_not_called()

    def test_utils_issues_create_github_issue_for_no_labels_provided(self, mocker):
        user = mocker.MagicMock()
        title, body = "title", "body text"
        client, repo, issue = mocker.MagicMock(), mocker.MagicMock(), mocker.MagicMock()
        client, repo = mocker.MagicMock(), mocker.MagicMock()
        mocked_client = mocker.patch("utils.issues._github_client", return_value=client)
        mocked_repo = mocker.patch("utils.issues._github_repository", return_value=repo)
        repo.create_issue.return_value = issue
        returned = create_github_issue(user, title, body)
        assert returned == {
            "success": True,
            "issue_number": issue.number,
            "issue_url": issue.html_url,
            "data": issue.raw_data,
        }
        mocked_client.assert_called_once_with(user)
        mocked_repo.assert_called_once_with(client)
        repo.create_issue.assert_called_once_with(title=title, body=body, labels=[])
        client.close.assert_called_once_with()

    def test_utils_issues_create_github_issue_functionality(self, mocker):
        user = mocker.MagicMock()
        title, body, labels = "title", "body text", ["label1", "label2"]
        client, repo, issue = mocker.MagicMock(), mocker.MagicMock(), mocker.MagicMock()
        client, repo = mocker.MagicMock(), mocker.MagicMock()
        mocked_client = mocker.patch("utils.issues._github_client", return_value=client)
        mocked_repo = mocker.patch("utils.issues._github_repository", return_value=repo)
        repo.create_issue.return_value = issue
        returned = create_github_issue(user, title, body, labels)
        assert returned == {
            "success": True,
            "issue_number": issue.number,
            "issue_url": issue.html_url,
            "data": issue.raw_data,
        }
        mocked_client.assert_called_once_with(user)
        mocked_repo.assert_called_once_with(client)
        repo.create_issue.assert_called_once_with(title=title, body=body, labels=labels)
        client.close.assert_called_once_with()
