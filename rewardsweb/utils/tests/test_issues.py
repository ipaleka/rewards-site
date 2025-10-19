"""Testing module for :py:mod:`utils.issues` module."""

from django.conf import settings

from utils.issues import (
    _github_client,
    _github_repository,
    _prepare_issue_body_from_contribution,
    _prepare_issue_labels_from_contribution,
    _prepare_issue_priority_from_contribution,
    _prepare_issue_title_from_contribution,
    add_labels_to_issue,
    close_issue_with_labels,
    create_github_issue,
    issue_data_for_contribution,
)


class TestUtilsIssuesGithubFunctions:
    """Testing class for :py:mod:`utils.issues` functions."""

    # # _github_client
    def test_utils_issues_github_client_for_no_token(self, mocker):
        user = mocker.MagicMock()
        user.profile.github_token = None
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
        user.profile.github_token = token
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

    # # add_labels_to_issue
    def test_utils_issues_add_labels_to_issue_for_no_client(self, mocker):
        user = mocker.MagicMock()
        mocked_client = mocker.patch("utils.issues._github_client", return_value=False)
        mocked_repo = mocker.patch("utils.issues._github_repository")
        returned = add_labels_to_issue(user, mocker.MagicMock(), mocker.MagicMock())
        assert returned == {
            "success": False,
            "error": "Please provide a GitHub access token in your profile page!",
        }
        mocked_client.assert_called_once_with(user)
        mocked_repo.assert_not_called()

    def test_utils_issues_add_labels_to_issue_for_error_on_issue_fetching(self, mocker):
        user = mocker.MagicMock()
        issue_number, labels = 505, ["label1"]
        client, repo = mocker.MagicMock(), mocker.MagicMock()
        mocked_client = mocker.patch("utils.issues._github_client", return_value=client)
        mocked_repo = mocker.patch("utils.issues._github_repository", return_value=repo)
        repo.get_issue.side_effect = Exception("Issue error")
        returned = add_labels_to_issue(user, issue_number, labels)
        assert returned == {"success": False, "error": "Issue error"}
        mocked_client.assert_called_once_with(user)
        mocked_repo.assert_called_once_with(client)
        repo.get_issue.assert_called_once_with(issue_number)
        client.close.assert_not_called()

    def test_utils_issues_add_labels_to_issue_functionality(self, mocker):
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
        returned = add_labels_to_issue(user, issue_number, labels)
        assert returned == {
            "success": True,
            "message": f"Added labels {labels} to issue #{issue_number}",
            "current_labels": ["name0", "name1", "name2"],
        }
        mocked_client.assert_called_once_with(user)
        mocked_repo.assert_called_once_with(client)
        repo.get_issue.assert_called_once_with(issue_number)
        issue.add_to_labels.assert_called_once_with("label1", "label2")
        client.close.assert_called_once_with()

    # # close_issue_with_labels
    def test_utils_issues_close_issue_with_labels_for_no_client(self, mocker):
        user = mocker.MagicMock()
        mocked_client = mocker.patch("utils.issues._github_client", return_value=False)
        mocked_repo = mocker.patch("utils.issues._github_repository")
        returned = close_issue_with_labels(user, mocker.MagicMock(), mocker.MagicMock())
        assert returned == {
            "success": False,
            "error": "Please provide a GitHub access token in your profile page!",
        }
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
        issue.add_to_labels.assert_not_called()
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
        issue.add_to_labels.assert_called_once_with("label1", "label2")
        issue.create_comment.assert_called_once_with(comment)
        issue.edit.assert_called_once_with(state="closed")
        client.close.assert_called_once_with()

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


class TestUtilsIssuesPrepareFunctions:
    """Testing class for :py:mod:`utils.issues` issue preparation functions."""

    # # _prepare_issue_body_from_contribution
    def test_utils_issues_prepare_issue_body_from_contribution_no_url(self, mocker):
        contribution = mocker.MagicMock()
        contribution.url = None

        result = _prepare_issue_body_from_contribution(contribution)

        assert result == "** Please provide the necessary information **"

    def test_utils_issues_prepare_issue_body_from_contribution_url_no_success(
        self, mocker
    ):
        contribution = mocker.MagicMock()
        contribution.url = "https://discord.com/channels/test"

        mocked_message_from_url = mocker.patch("utils.issues.message_from_url")
        mocked_message_from_url.return_value = {"success": False}

        result = _prepare_issue_body_from_contribution(contribution)

        assert result == "** Please provide the necessary information **"
        mocked_message_from_url.assert_called_once_with(contribution.url)

    def test_utils_issues_prepare_issue_body_from_contribution_successful_parsing(
        self, mocker
    ):
        contribution = mocker.MagicMock()
        contribution.url = "https://discord.com/channels/test"

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

        result = _prepare_issue_body_from_contribution(contribution)

        expected_body = "By testuser on 15 Oct 14:30 in [Discord](https://discord.com/channels/test):\n> This is a test message\n> with multiple lines\n"
        assert result == expected_body
        mocked_message_from_url.assert_called_once_with(contribution.url)
        mocked_datetime.strptime.assert_called_once_with(
            "2023-10-15T14:30:00.000000+00:00", "%Y-%m-%dT%H:%M:%S.%f%z"
        )

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
        contribution = mocker.MagicMock()

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

        result = issue_data_for_contribution(contribution)

        expected_data = {
            "issue_title": "Test Title",
            "issue_body": "Test Body",
            "labels": ["bug"],
            "priority": "high priority",
        }
        assert result == expected_data

    def test_utils_issues_issue_data_for_contribution_calls_all_helpers(self, mocker):
        contribution = mocker.MagicMock()

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

        issue_data_for_contribution(contribution)

        mocked_title.assert_called_once_with(contribution)
        mocked_body.assert_called_once_with(contribution)
        mocked_labels.assert_called_once_with(contribution)
        mocked_priority.assert_called_once_with(contribution)
