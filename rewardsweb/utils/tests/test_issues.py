"""Testing module for :py:mod:`utils.issues` module."""

from django.conf import settings

from utils.issues import (
    GitHubApp,
    _contributor_link,
    _github_client,
    _github_repository,
    _prepare_issue_body_from_contribution,
    _prepare_issue_labels_from_contribution,
    _prepare_issue_priority_from_contribution,
    _prepare_issue_title_from_contribution,
    fetch_issues,
    set_labels_to_issue,
    close_issue_with_labels,
    create_github_issue,
    issue_by_number,
    issue_data_for_contribution,
)
from utils.constants.core import GITHUB_ISSUES_START_DATE
from utils.constants.ui import MISSING_TOKEN_TEXT


class TestUtilsIssuesGitHubApp:
    """Testing class for :py:mod:`utils.issues.GitHubApp` class."""

    def test_utils_issues_githubapp_jwt_token_no_env_vars(self, mocker):
        mocked_get_env_variable = mocker.patch(
            "utils.issues.get_env_variable", return_value=""
        )
        instance = GitHubApp()
        assert instance.jwt_token() is None
        mocked_get_env_variable.assert_has_calls(
            [
                mocker.call("GITHUB_BOT_PRIVATE_KEY_FILENAME", ""),
                mocker.call("GITHUB_BOT_CLIENT_ID", ""),
            ]
        )

    def test_utils_issues_githubapp_jwt_token_success(self, mocker):
        mocked_get_env_variable = mocker.patch(
            "utils.issues.get_env_variable",
            side_effect=["test.pem", "test_id"],
        )
        mock_settings = mocker.MagicMock()
        mock_settings.BASE_DIR.parent = mocker.MagicMock()
        mocker.patch("utils.issues.settings", mock_settings)
        mock_open = mocker.mock_open(read_data=b"test_key")
        mocker.patch("builtins.open", mock_open)
        mock_datetime = mocker.MagicMock()
        mock_timedelta = mocker.MagicMock()
        mocker.patch("utils.issues.datetime", mock_datetime)
        mocker.patch("utils.issues.timedelta", mock_timedelta)
        mock_jwt = mocker.MagicMock()
        mocker.patch("utils.issues.jwt", mock_jwt)

        instance = GitHubApp()
        instance.jwt_token()

        mocked_get_env_variable.assert_has_calls(
            [
                mocker.call("GITHUB_BOT_PRIVATE_KEY_FILENAME", ""),
                mocker.call("GITHUB_BOT_CLIENT_ID", ""),
            ]
        )
        mock_open.assert_called_once_with(
            mock_settings.BASE_DIR.parent / "fixtures" / "test.pem", "rb"
        )
        mock_jwt.encode.assert_called_once()

    def test_utils_issues_githubapp_installation_token_no_id(self, mocker):
        mocked_get_env_variable = mocker.patch(
            "utils.issues.get_env_variable", return_value=""
        )
        instance = GitHubApp()
        assert instance.installation_token() is None
        mocked_get_env_variable.assert_called_once_with(
            "GITHUB_BOT_INSTALLATION_ID", ""
        )

    def test_utils_issues_githubapp_installation_token_no_jwt(self, mocker):
        mocker.patch("utils.issues.get_env_variable", return_value="test_id")
        mock_jwt_token = mocker.patch.object(GitHubApp, "jwt_token", return_value=None)
        instance = GitHubApp()
        assert instance.installation_token() is None
        mock_jwt_token.assert_called_once_with()

    def test_utils_issues_githubapp_installation_token_request_fails(self, mocker):
        mocker.patch("utils.issues.get_env_variable", return_value="test_id")
        mocker.patch.object(GitHubApp, "jwt_token", return_value="test_jwt")
        mock_response = mocker.MagicMock()
        mock_response.status_code = 400
        mocked_requests = mocker.patch(
            "utils.issues.requests.post", return_value=mock_response
        )
        instance = GitHubApp()
        assert instance.installation_token() is None
        mocked_requests.assert_called_once()

    def test_utils_issues_githubapp_installation_token_success(self, mocker):
        mocker.patch("utils.issues.get_env_variable", return_value="test_id")
        mocker.patch.object(GitHubApp, "jwt_token", return_value="test_jwt")
        mock_response = mocker.MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"token": "test_token"}
        mocked_requests = mocker.patch(
            "utils.issues.requests.post", return_value=mock_response
        )
        instance = GitHubApp()
        assert instance.installation_token() == "test_token"
        mocked_requests.assert_called_once()

    def test_utils_issues_githubapp_client_no_token(self, mocker):
        mock_installation_token = mocker.patch.object(
            GitHubApp, "installation_token", return_value=None
        )
        mocked_github = mocker.patch("utils.issues.Github")
        instance = GitHubApp()
        assert instance.client() is None
        mock_installation_token.assert_called_once_with()
        mocked_github.assert_not_called()

    def test_utils_issues_githubapp_client_success(self, mocker):
        mock_installation_token = mocker.patch.object(
            GitHubApp, "installation_token", return_value="test_token"
        )
        mock_github_instance = mocker.MagicMock()
        mocked_github = mocker.patch(
            "utils.issues.Github", return_value=mock_github_instance
        )
        instance = GitHubApp()
        assert instance.client() == mock_github_instance
        mock_installation_token.assert_called_once_with()
        mocked_github.assert_called_once_with("test_token")


class TestUtilsIssuesHelperFunctions:
    """Testing class for :py:mod:`utils.issues` helper functions."""

    # # contributor_link
    def test_utils_issues_contributor_link_for_contributor_not_found(self, mocker):
        handle = "handle"
        mocked_contributor = mocker.patch(
            "utils.issues.Contributor.objects.from_handle", return_value=None
        )
        returned = _contributor_link(handle)
        assert returned == handle
        mocked_contributor.assert_called_once_with(handle)

    def test_utils_issues_contributor_link_for_error(self, mocker):
        handle = "handle"
        mocked_contributor = mocker.patch(
            "utils.issues.Contributor.objects.from_handle",
            side_effect=ValueError("error"),
        )
        returned = _contributor_link(handle)
        assert returned == handle
        mocked_contributor.assert_called_once_with(handle)

    def test_utils_issues_contributor_link_functionality(self, mocker):
        handle = "handle"
        contributor = mocker.MagicMock()
        url = "http://example.com"
        contributor.get_absolute_url.return_value = url
        mocked_contributor = mocker.patch(
            "utils.issues.Contributor.objects.from_handle", return_value=contributor
        )
        returned = _contributor_link(handle)
        assert returned == f"[{handle}]({url})"
        mocked_contributor.assert_called_once_with(handle)


class TestUtilsIssuesCrudFunctions:
    """Testing class for :py:mod:`utils.issues` CRUD functions."""

    # # _github_client
    def test_utils_issues_github_client_for_no_client_and_token(self, mocker):
        mcok_user = mocker.MagicMock()
        mcok_user.profile.github_token = None
        mock_githubapp = mocker.MagicMock()
        mock_githubapp.client.return_value = None
        mocked_githubapp = mocker.patch(
            "utils.issues.GitHubApp", return_value=mock_githubapp
        )
        mocked_token = mocker.patch("utils.issues.Auth.Token")
        returned = _github_client(mcok_user)
        assert returned is False
        mocked_githubapp.assert_called_once_with()
        mocked_token.assert_not_called()

    def test_utils_issues_github_client_for_githubapp_client(self, mocker):
        mock_user = mocker.MagicMock()
        mock_githubapp = mocker.MagicMock()
        mock_client = mocker.MagicMock()
        mock_githubapp.client.return_value = mock_client
        mocked_githubapp = mocker.patch(
            "utils.issues.GitHubApp", return_value=mock_githubapp
        )
        mocked_token = mocker.patch("utils.issues.Auth.Token")
        returned = _github_client(mock_user)
        assert returned == mock_client
        mocked_githubapp.assert_called_once_with()
        mocked_token.assert_not_called()

    def test_utils_issues_github_client_for_user_token(self, mocker):
        mock_user = mocker.MagicMock()
        mock_token = mocker.MagicMock()
        mock_auth, mock_client = mocker.MagicMock(), mocker.MagicMock()
        mock_githubapp = mocker.MagicMock()
        mock_githubapp.client.return_value = None
        mocked_githubapp = mocker.patch(
            "utils.issues.GitHubApp", return_value=mock_githubapp
        )
        mocked_auth = mocker.patch("utils.issues.Auth.Token", return_value=mock_auth)
        mocked_github = mocker.patch("utils.issues.Github", return_value=mock_client)
        mock_user.profile.github_token = mock_token
        returned = _github_client(mock_user)
        assert returned == mock_client
        mocked_githubapp.assert_called_once_with()
        mocked_auth.assert_called_once_with(mock_token)
        mocked_github.assert_called_once_with(auth=mock_auth)

    # # _github_repository
    def test_utils_issues_github_repository_functionality(self, mocker):
        client = mocker.MagicMock()
        returned = _github_repository(client)
        assert returned == client.get_repo.return_value
        client.get_repo.assert_called_once_with(
            f"{settings.GITHUB_REPO_OWNER}/{settings.GITHUB_REPO_NAME}"
        )

    # # fetch_issues
    def test_utils_issues_fetch_issues_no_client(self, mocker):
        """Test handling when GitHub client creation fails."""
        github_token = "test_token"
        mock_auth = mocker.MagicMock()

        mocked_auth = mocker.patch("utils.issues.Auth.Token", return_value=mock_auth)
        mocked_github = mocker.patch("utils.issues.Github", return_value=None)

        result = fetch_issues(github_token)

        assert result == []
        mocked_auth.assert_called_once_with(github_token)
        mocked_github.assert_called_once_with(auth=mock_auth)

    def test_utils_issues_fetch_issues_success(self, mocker):
        """Test successful retrieval of all issues."""
        github_token = "test_token"
        mock_auth = mocker.MagicMock()
        mock_client = mocker.MagicMock()
        mock_repo = mocker.MagicMock()
        mock_issues = mocker.MagicMock()
        mocked_auth = mocker.patch("utils.issues.Auth.Token", return_value=mock_auth)
        mocked_github = mocker.patch("utils.issues.Github", return_value=mock_client)
        mocked_repo = mocker.patch(
            "utils.issues._github_repository", return_value=mock_repo
        )
        mock_repo.get_issues.return_value = mock_issues

        result = fetch_issues(github_token)

        assert result == mock_issues
        mocked_auth.assert_called_once_with(github_token)
        mocked_github.assert_called_once_with(auth=mock_auth)
        mocked_repo.assert_called_once_with(mock_client)
        mock_repo.get_issues.assert_called_once_with(
            state="all", sort="updated", direction="asc", since=GITHUB_ISSUES_START_DATE
        )

    def test_utils_issues_fetch_issues_success_provided_arguments(self, mocker):
        """Test successful retrieval of all issues."""
        github_token = "test_token"
        mock_auth = mocker.MagicMock()
        mock_client = mocker.MagicMock()
        mock_repo = mocker.MagicMock()
        mock_issues = mocker.MagicMock()

        mocked_auth = mocker.patch("utils.issues.Auth.Token", return_value=mock_auth)
        mocked_github = mocker.patch("utils.issues.Github", return_value=mock_client)
        mocked_repo = mocker.patch(
            "utils.issues._github_repository", return_value=mock_repo
        )
        mock_repo.get_issues.return_value = mock_issues
        since = mocker.MagicMock()
        result = fetch_issues(github_token, state="closed", since=since)

        assert result == mock_issues
        mocked_auth.assert_called_once_with(github_token)
        mocked_github.assert_called_once_with(auth=mock_auth)
        mocked_repo.assert_called_once_with(mock_client)
        mock_repo.get_issues.assert_called_once_with(
            state="closed", sort="updated", direction="asc", since=since
        )

    # # close_issue_with_labels
    def test_utils_issues_close_issue_with_labels_for_no_client(self, mocker):
        user = mocker.MagicMock()
        mocked_client = mocker.patch("utils.issues._github_client", return_value=False)
        mocked_repo = mocker.patch("utils.issues._github_repository")
        returned = close_issue_with_labels(user, mocker.MagicMock(), mocker.MagicMock())
        assert returned == {"success": False, "error": MISSING_TOKEN_TEXT}
        mocked_client.assert_called_once_with(user)
        mocked_repo.assert_not_called()

    def test_utils_issues_close_issue_with_labels_for_error_on_issue_fetching(
        self, mocker
    ):
        user = mocker.MagicMock()
        issue_number, labels = 505, ["label1"]
        client, repo = mocker.MagicMock(), mocker.MagicMock()
        mocked_client = mocker.patch("utils.issues._github_client", return_value=client)
        mocked_repo = mocker.patch("utils.issues._github_repository", return_value=repo)
        repo.get_issue.side_effect = Exception("Issue error")
        returned = close_issue_with_labels(user, issue_number, labels)
        assert returned == {"success": False, "error": "Issue error"}
        mocked_client.assert_called_once_with(user)
        mocked_repo.assert_called_once_with(client)
        repo.get_issue.assert_called_once_with(issue_number)
        client.close.assert_not_called()

    def test_utils_issues_close_issue_with_labels_for_no_labels_and_comment(
        self, mocker
    ):
        user = mocker.MagicMock()
        issue_number = 505
        client, repo = mocker.MagicMock(), mocker.MagicMock()
        mocked_client = mocker.patch("utils.issues._github_client", return_value=client)
        mocked_repo = mocker.patch("utils.issues._github_repository", return_value=repo)
        issue = mocker.MagicMock()
        label0, label1, label2 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        label0.name = "name0"
        label1.name = "name1"
        label2.name = "name2"
        issue.labels = [label0, label1, label2]
        issue.state = "state"
        repo.get_issue.return_value = issue
        returned = close_issue_with_labels(user, issue_number)
        assert returned == {
            "success": True,
            "message": f"Closed issue #{issue_number} with labels None",
            "issue_state": issue.state,
            "current_labels": ["name0", "name1", "name2"],
        }
        mocked_client.assert_called_once_with(user)
        mocked_repo.assert_called_once_with(client)
        repo.get_issue.assert_called_once_with(issue_number)
        issue.edit.assert_called_once_with(state="closed")
        client.close.assert_called_once_with()
        issue.set_labels.assert_not_called()
        issue.create_comment.assert_not_called()

    def test_utils_issues_close_issue_with_labels_functionality(self, mocker):
        user = mocker.MagicMock()
        issue_number, labels = 505, ["label1", "label2"]
        client, repo = mocker.MagicMock(), mocker.MagicMock()
        mocked_client = mocker.patch("utils.issues._github_client", return_value=client)
        mocked_repo = mocker.patch("utils.issues._github_repository", return_value=repo)
        issue = mocker.MagicMock()
        label0, label1, label2 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        label0.name = "name0"
        label1.name = "name1"
        label2.name = "name2"
        issue.labels = [label0, label1, label2]
        issue.state = "state"
        repo.get_issue.return_value = issue
        comment = "comment"
        returned = close_issue_with_labels(user, issue_number, labels, comment)
        assert returned == {
            "success": True,
            "message": f"Closed issue #{issue_number} with labels {labels}",
            "issue_state": issue.state,
            "current_labels": ["name0", "name1", "name2"],
        }
        mocked_client.assert_called_once_with(user)
        mocked_repo.assert_called_once_with(client)
        repo.get_issue.assert_called_once_with(issue_number)
        issue.set_labels.assert_called_once_with("label1", "label2")
        issue.create_comment.assert_called_once_with(comment)
        issue.edit.assert_called_once_with(state="closed")
        client.close.assert_called_once_with()

    # # create_github_issue
    def test_utils_issues_create_github_issue_for_no_client(self, mocker):
        user = mocker.MagicMock()
        mocked_client = mocker.patch("utils.issues._github_client", return_value=False)
        mocked_repo = mocker.patch("utils.issues._github_repository")
        returned = create_github_issue(user, mocker.MagicMock(), mocker.MagicMock())
        assert returned == {"success": False, "error": MISSING_TOKEN_TEXT}
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

    # # issue_by_number
    def test_utils_issues_issue_by_number_for_no_client(self, mocker):
        user = mocker.MagicMock()
        mocked_client = mocker.patch("utils.issues._github_client", return_value=False)
        mocked_repo = mocker.patch("utils.issues._github_repository")
        returned = issue_by_number(user, mocker.MagicMock())
        assert returned == {"success": False, "error": MISSING_TOKEN_TEXT}
        mocked_client.assert_called_once_with(user)
        mocked_repo.assert_not_called()

    def test_utils_issues_issue_by_number_for_error_on_issue_fetching(self, mocker):
        user = mocker.MagicMock()
        issue_number = 505
        client, repo = mocker.MagicMock(), mocker.MagicMock()
        mocked_client = mocker.patch("utils.issues._github_client", return_value=client)
        mocked_repo = mocker.patch("utils.issues._github_repository", return_value=repo)
        repo.get_issue.side_effect = Exception("Issue error")
        returned = issue_by_number(user, issue_number)
        assert returned == {"success": False, "error": "Issue error"}
        mocked_client.assert_called_once_with(user)
        mocked_repo.assert_called_once_with(client)
        repo.get_issue.assert_called_once_with(issue_number)
        client.close.assert_not_called()

    def test_utils_issues_issue_by_number_functionality(self, mocker):
        user = mocker.MagicMock()
        issue_number = 505
        client, repo = mocker.MagicMock(), mocker.MagicMock()
        mocked_client = mocker.patch("utils.issues._github_client", return_value=client)
        mocked_repo = mocker.patch("utils.issues._github_repository", return_value=repo)

        # Mock issue and its properties
        issue = mocker.MagicMock()
        issue.number = issue_number
        issue.title = "Test Issue Title"
        issue.body = "Test Issue Body"
        issue.state = "open"
        issue.created_at = mocker.MagicMock()
        issue.updated_at = mocker.MagicMock()
        issue.closed_at = None
        issue.html_url = "https://github.com/owner/repo/issues/505"
        issue.comments = 3

        # Mock labels
        label1, label2 = mocker.MagicMock(), mocker.MagicMock()
        label1.name = "bug"
        label2.name = "enhancement"
        issue.labels = [label1, label2]

        # Mock assignees
        assignee1, assignee2 = mocker.MagicMock(), mocker.MagicMock()
        assignee1.login = "user1"
        assignee2.login = "user2"
        issue.assignees = [assignee1, assignee2]

        # Mock user
        issue_user = mocker.MagicMock()
        issue_user.login = "issue_creator"
        issue.user = issue_user

        repo.get_issue.return_value = issue

        returned = issue_by_number(user, issue_number)

        expected_issue_data = {
            "number": issue_number,
            "title": "Test Issue Title",
            "body": "Test Issue Body",
            "state": "open",
            "created_at": issue.created_at,
            "updated_at": issue.updated_at,
            "closed_at": None,
            "labels": ["bug", "enhancement"],
            "assignees": ["user1", "user2"],
            "user": "issue_creator",
            "html_url": "https://github.com/owner/repo/issues/505",
            "comments": 3,
        }

        assert returned == {
            "success": True,
            "message": f"Retrieved issue #{issue_number}",
            "issue": expected_issue_data,
        }
        mocked_client.assert_called_once_with(user)
        mocked_repo.assert_called_once_with(client)
        repo.get_issue.assert_called_once_with(issue_number)
        client.close.assert_called_once_with()

    def test_utils_issues_issue_by_number_with_none_dates(self, mocker):
        user = mocker.MagicMock()
        issue_number = 505
        client, repo = mocker.MagicMock(), mocker.MagicMock()
        mocked_client = mocker.patch("utils.issues._github_client", return_value=client)
        mocked_repo = mocker.patch("utils.issues._github_repository", return_value=repo)

        # Mock issue with None dates
        issue = mocker.MagicMock()
        issue.number = issue_number
        issue.title = "Test Issue"
        issue.body = "Test Body"
        issue.state = "open"
        issue.created_at = None
        issue.updated_at = None
        issue.closed_at = None
        issue.html_url = "https://github.com/owner/repo/issues/505"
        issue.comments = 0
        issue.labels = []
        issue.assignees = []
        issue.user = None

        repo.get_issue.return_value = issue

        returned = issue_by_number(user, issue_number)

        expected_issue_data = {
            "number": issue_number,
            "title": "Test Issue",
            "body": "Test Body",
            "state": "open",
            "created_at": None,
            "updated_at": None,
            "closed_at": None,
            "labels": [],
            "assignees": [],
            "user": None,
            "html_url": "https://github.com/owner/repo/issues/505",
            "comments": 0,
        }

        assert returned == {
            "success": True,
            "message": f"Retrieved issue #{issue_number}",
            "issue": expected_issue_data,
        }
        mocked_client.assert_called_once_with(user)
        mocked_repo.assert_called_once_with(client)
        repo.get_issue.assert_called_once_with(issue_number)
        client.close.assert_called_once_with()

    # # set_labels_to_issue
    def test_utils_issues_set_labels_to_issue_for_no_client(self, mocker):
        user = mocker.MagicMock()
        mocked_client = mocker.patch("utils.issues._github_client", return_value=False)
        mocked_repo = mocker.patch("utils.issues._github_repository")
        returned = set_labels_to_issue(user, mocker.MagicMock(), mocker.MagicMock())
        assert returned == {"success": False, "error": MISSING_TOKEN_TEXT}
        mocked_client.assert_called_once_with(user)
        mocked_repo.assert_not_called()

    def test_utils_issues_set_labels_to_issue_for_error_on_issue_fetching(self, mocker):
        user = mocker.MagicMock()
        issue_number, labels = 505, ["label1"]
        client, repo = mocker.MagicMock(), mocker.MagicMock()
        mocked_client = mocker.patch("utils.issues._github_client", return_value=client)
        mocked_repo = mocker.patch("utils.issues._github_repository", return_value=repo)
        repo.get_issue.side_effect = Exception("Issue error")
        returned = set_labels_to_issue(user, issue_number, labels)
        assert returned == {"success": False, "error": "Issue error"}
        mocked_client.assert_called_once_with(user)
        mocked_repo.assert_called_once_with(client)
        repo.get_issue.assert_called_once_with(issue_number)
        client.close.assert_not_called()

    def test_utils_issues_set_labels_to_issue_functionality(self, mocker):
        user = mocker.MagicMock()
        issue_number, labels = 505, ["label1", "label2"]
        client, repo = mocker.MagicMock(), mocker.MagicMock()
        mocked_client = mocker.patch("utils.issues._github_client", return_value=client)
        mocked_repo = mocker.patch("utils.issues._github_repository", return_value=repo)
        issue = mocker.MagicMock()
        label0, label1, label2 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        label0.name = "name0"
        label1.name = "name1"
        label2.name = "name2"
        issue.labels = [label0, label1, label2]
        repo.get_issue.return_value = issue
        returned = set_labels_to_issue(user, issue_number, labels)
        assert returned == {
            "success": True,
            "message": f"Added labels {labels} to issue #{issue_number}",
            "current_labels": ["name0", "name1", "name2"],
        }
        mocked_client.assert_called_once_with(user)
        mocked_repo.assert_called_once_with(client)
        repo.get_issue.assert_called_once_with(issue_number)
        issue.set_labels.assert_called_once_with("label1", "label2")
        client.close.assert_called_once_with()


class TestUtilsIssuesPrepareFunctions:
    """Testing class for :py:mod:`utils.issues` issue preparation functions."""

    # # _prepare_issue_body_from_contribution
    def test_utils_issues_prepare_issue_body_from_contribution_no_url(self, mocker):
        contribution, profile = mocker.MagicMock(), mocker.MagicMock()
        contribution.url = None
        mocked_link = mocker.patch("utils.issues._contributor_link")

        result = _prepare_issue_body_from_contribution(contribution, profile)

        assert result == "** Please provide the necessary information **"
        mocked_link.assert_not_called()

    def test_utils_issues_prepare_issue_body_from_contribution_url_no_success(
        self, mocker
    ):
        contribution, profile = mocker.MagicMock(), mocker.MagicMock()
        contribution.url = "https://discord.com/channels/test"
        mocked_link = mocker.patch("utils.issues._contributor_link")

        mocked_message_from_url = mocker.patch("utils.issues.message_from_url")
        mocked_message_from_url.return_value = {"success": False}

        result = _prepare_issue_body_from_contribution(contribution, profile)

        assert result == "** Please provide the necessary information **"
        mocked_message_from_url.assert_called_once_with(contribution.url)
        mocked_link.assert_not_called()

    def test_utils_issues_prepare_issue_body_from_contribution_successful_parsing(
        self, mocker
    ):
        contribution, profile = mocker.MagicMock(), "username"
        contribution.url = "https://discord.com/channels/test"
        link = "https://example.com"
        mocked_link = mocker.patch("utils.issues._contributor_link", return_value=link)

        test_message = {
            "success": True,
            "author": "testuser",
            "timestamp": "2023-10-15T14:30:00.000000+00:00",
            "content": "This is a test message\nwith multiple lines",
        }

        mocked_message_from_url = mocker.patch("utils.issues.message_from_url")
        mocked_message_from_url.return_value = test_message
        mocked_datetime = mocker.patch("utils.issues.datetime")
        mocked_datetime.strptime.return_value.strftime.return_value = "15 Oct 14:30"

        result = _prepare_issue_body_from_contribution(contribution, profile)

        expected_body = (
            f"By {link} on 15 Oct 14:30 in [Discord](https://discord.com/channels/test): "
            f"// su: {profile}\n> This is a test message\n> with multiple lines\n"
        )
        assert result == expected_body
        mocked_message_from_url.assert_called_once_with(contribution.url)
        mocked_datetime.strptime.assert_called_once_with(
            "2023-10-15T14:30:00.000000+00:00", "%Y-%m-%dT%H:%M:%S.%f%z"
        )
        mocked_link.assert_called_once_with(test_message.get("author"))

    # # _prepare_issue_labels_from_contribution
    def test_utils_issues_prepare_issue_labels_bug_type(self, mocker):
        contribution = mocker.MagicMock()
        reward_type = mocker.MagicMock()
        reward_type.name = "Bug Fix"
        contribution.reward.type = reward_type

        result = _prepare_issue_labels_from_contribution(contribution)

        assert result == ["bug"]

    def test_utils_issues_prepare_issue_labels_feature_type(self, mocker):
        contribution = mocker.MagicMock()
        reward_type = mocker.MagicMock()
        reward_type.name = "Feature Request"
        contribution.reward.type = reward_type

        result = _prepare_issue_labels_from_contribution(contribution)

        assert result == ["feature"]

    def test_utils_issues_prepare_issue_labels_task_type(self, mocker):
        contribution = mocker.MagicMock()
        reward_type = mocker.MagicMock()
        reward_type.name = "General Task"
        contribution.reward.type = reward_type

        result = _prepare_issue_labels_from_contribution(contribution)

        assert result == ["task"]

    def test_utils_issues_prepare_issue_labels_twitter_type(self, mocker):
        contribution = mocker.MagicMock()
        reward_type = mocker.MagicMock()
        reward_type.name = "Twitter Engagement"
        contribution.reward.type = reward_type

        result = _prepare_issue_labels_from_contribution(contribution)

        assert result == ["task"]

    def test_utils_issues_prepare_issue_labels_research_type(self, mocker):
        contribution = mocker.MagicMock()
        reward_type = mocker.MagicMock()
        reward_type.name = "Research Work"
        contribution.reward.type = reward_type

        result = _prepare_issue_labels_from_contribution(contribution)

        assert result == ["research"]

    def test_utils_issues_prepare_issue_labels_unknown_type(self, mocker):
        contribution = mocker.MagicMock()
        reward_type = mocker.MagicMock()
        reward_type.name = "Unknown Type"
        contribution.reward.type = reward_type

        result = _prepare_issue_labels_from_contribution(contribution)

        assert result == []

    # # _prepare_issue_priority_from_contribution
    def test_utils_issues_prepare_issue_priority_bug_type(self, mocker):
        contribution = mocker.MagicMock()
        reward_type = mocker.MagicMock()
        reward_type.name = "Critical Bug"
        contribution.reward.type = reward_type

        result = _prepare_issue_priority_from_contribution(contribution)

        assert result == "high priority"

    def test_utils_issues_prepare_issue_priority_non_bug_type(self, mocker):
        contribution = mocker.MagicMock()
        reward_type = mocker.MagicMock()
        reward_type.name = "Feature Implementation"
        contribution.reward.type = reward_type

        result = _prepare_issue_priority_from_contribution(contribution)

        assert result == "medium priority"

    # # _prepare_issue_title_from_contribution
    def test_utils_issues_prepare_issue_title_with_comment(self, mocker):
        contribution = mocker.MagicMock()
        reward_type = mocker.MagicMock()
        reward_type.label = "FEAT"
        contribution.reward.type = reward_type
        contribution.reward.level = "A"
        contribution.comment = "Implement new authentication system"

        result = _prepare_issue_title_from_contribution(contribution)

        expected_title = "[FEATA] Implement new authentication system"
        assert result == expected_title

    def test_utils_issues_prepare_issue_title_without_comment(self, mocker):
        contribution = mocker.MagicMock()
        reward_type = mocker.MagicMock()
        reward_type.label = "BUG"
        contribution.reward.type = reward_type
        contribution.reward.level = "B"
        contribution.comment = ""

        result = _prepare_issue_title_from_contribution(contribution)

        expected_title = "[BUGB] "
        assert result == expected_title

    # # issue_data_for_contribution
    def test_utils_issues_issue_data_for_contribution_complete_data(self, mocker):
        contribution, profile = mocker.MagicMock(), mocker.MagicMock()

        # Mock all the helper functions
        mocker.patch(
            "utils.issues._prepare_issue_title_from_contribution",
            return_value="Test Title",
        )
        mocker.patch(
            "utils.issues._prepare_issue_body_from_contribution",
            return_value="Test Body",
        )
        mocker.patch(
            "utils.issues._prepare_issue_labels_from_contribution", return_value=["bug"]
        )
        mocker.patch(
            "utils.issues._prepare_issue_priority_from_contribution",
            return_value="high priority",
        )

        result = issue_data_for_contribution(contribution, profile)

        expected_data = {
            "issue_title": "Test Title",
            "issue_body": "Test Body",
            "labels": ["bug"],
            "priority": "high priority",
        }
        assert result == expected_data

    def test_utils_issues_issue_data_for_contribution_calls_all_helpers(self, mocker):
        contribution, profile = mocker.MagicMock(), mocker.MagicMock()

        mocked_title = mocker.patch(
            "utils.issues._prepare_issue_title_from_contribution"
        )
        mocked_body = mocker.patch("utils.issues._prepare_issue_body_from_contribution")
        mocked_labels = mocker.patch(
            "utils.issues._prepare_issue_labels_from_contribution"
        )
        mocked_priority = mocker.patch(
            "utils.issues._prepare_issue_priority_from_contribution"
        )

        issue_data_for_contribution(contribution, profile)

        mocked_title.assert_called_once_with(contribution)
        mocked_body.assert_called_once_with(contribution, profile)
        mocked_labels.assert_called_once_with(contribution)
        mocked_priority.assert_called_once_with(contribution)
