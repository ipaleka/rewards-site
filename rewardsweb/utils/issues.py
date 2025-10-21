"""Module containing functions for GitHub issues management."""

import logging
from datetime import datetime

from django.conf import settings
from github import Auth, Github

from utils.bot import message_from_url
from utils.constants.ui import MISSING_TOKEN_TEXT

logger = logging.getLogger(__name__)


# # CRUD
def _github_client(user):
    """Instantiate and return GitHub client instance on behalf `user`.

    :param user: Django user instance
    :type user: class:`django.contrib.auth.models.User`
    :var github_token: GitHub user's access token
    :type github_token: str
    :var auth: GitHub authentication token instance
    :type auth: :class:`github.Github`
    :return: :class:`github.Github
    """
    github_token = user.profile.github_token
    if not github_token:
        return False

    auth = Auth.Token(github_token)

    return Github(auth=auth)


def _github_repository(client):
    """Return instance of GitHub repository holding project's issues.

    :param client: GitHub client instance
    :type client: :class:`github.Github`
    :return: :class:`github.Repository.Repository`
    """
    return client.get_repo(f"{settings.GITHUB_REPO_OWNER}/{settings.GITHUB_REPO_NAME}")


def add_labels_to_issue(user, issue_number, labels_to_add):
    """Add provided `labels` to the issue defined by `issue_number` on behalf `user`.

    :param user: Django user instance
    :type user: class:`django.contrib.auth.models.User`
    :param issue_number: unique issue's number
    :type issue_number: int
    :param labels_to_add: collection of GitHub labels to add to the issue
    :type labels_to_add: list
    :var client: GitHub client instance
    :type client: :class:`github.Github`
    :var repo: GitHub repository instance
    :type repo: :class:`github.Repository.Repository`
    :var issue: GitHub issue instance
    :type issue: :class:`github.Issue.Issue`
    :return: dict
    """
    try:
        client = _github_client(user)
        if not client:
            return {"success": False, "error": MISSING_TOKEN_TEXT}

        repo = _github_repository(client)
        issue = repo.get_issue(issue_number)

        # Add labels to the issue
        issue.add_to_labels(*labels_to_add)

        client.close()

        return {
            "success": True,
            "message": f"Added labels {labels_to_add} to issue #{issue_number}",
            "current_labels": [label.name for label in issue.labels],
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def close_issue_with_labels(user, issue_number, labels_to_add=None, comment=None):
    """Close GitHub issue defined by `issue_number` on behalf `user`.

    :param user: Django user instance
    :type user: class:`django.contrib.auth.models.User`
    :param issue_number: unique issue's number
    :type issue_number: int
    :param body: formatted issue's body text
    :type body: str
    :param labels_to_add: collection of GitHub labels to add to the issue
    :type labels_to_add: list
    :var comment: text to add as a GitHub comment
    :type comment: str
    :var client: GitHub client instance
    :type client: :class:`github.Github`
    :var repo: GitHub repository instance
    :type repo: :class:`github.Repository.Repository`
    :var issue: GitHub issue instance
    :type issue: :class:`github.Issue.Issue`
    :return: dict
    """
    try:
        client = _github_client(user)
        if not client:
            return {"success": False, "error": MISSING_TOKEN_TEXT}

        repo = _github_repository(client)
        issue = repo.get_issue(issue_number)

        # Add labels if provided
        if labels_to_add:
            issue.add_to_labels(*labels_to_add)

        # Add comment if provided
        if comment:
            issue.create_comment(comment)

        # Close the issue
        issue.edit(state="closed")

        client.close()

        return {
            "success": True,
            "message": f"Closed issue #{issue_number} with labels {labels_to_add}",
            "issue_state": issue.state,
            "current_labels": [label.name for label in issue.labels],
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def create_github_issue(user, title, body, labels=None):
    """Create GitHub issue on behalf `user` defined by provided arguments.

    :param user: Django user instance
    :type user: class:`django.contrib.auth.models.User`
    :param title: issue's title
    :type title: str
    :param body: formatted issue's body text
    :type body: str
    :param labels: collection of GitHub labels to assin to the issue
    :type labels: list
    :var client: GitHub client instance
    :type client: :class:`github.Github`
    :var repo: GitHub repository instance
    :type repo: :class:`github.Repository.Repository`
    :var issue: GitHub issue instance
    :type issue: :class:`github.Issue.Issue`
    :return: dict
    """
    try:
        client = _github_client(user)
        if not client:
            return {"success": False, "error": MISSING_TOKEN_TEXT}

        repo = _github_repository(client)

        # Create issue
        issue = repo.create_issue(title=title, body=body, labels=labels or [])

        client.close()

        return {
            "success": True,
            "issue_number": issue.number,
            "issue_url": issue.html_url,
            "data": issue.raw_data,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def issue_by_number(user, issue_number):
    """Retrieve the issue defined by `issue_number` on behalf `user`.

    :param user: Django user instance
    :type user: class:`django.contrib.auth.models.User`
    :param issue_number: unique issue's number
    :type issue_number: int
    :var client: GitHub client instance
    :type client: :class:`github.Github`
    :var repo: GitHub repository instance
    :type repo: :class:`github.Repository.Repository`
    :var issue: GitHub issue instance
    :type issue: :class:`github.Issue.Issue`
    :return: dict
    """
    try:
        client = _github_client(user)
        if not client:
            return {"success": False, "error": MISSING_TOKEN_TEXT}

        repo = _github_repository(client)
        issue = repo.get_issue(issue_number)

        # Convert issue to dict with relevant information
        issue_data = {
            "number": issue.number,
            "title": issue.title,
            "body": issue.body,
            "state": issue.state,
            "created_at": issue.created_at,  # Keep as datetime object
            "updated_at": issue.updated_at,  # Keep as datetime object
            "closed_at": issue.closed_at,  # Keep as datetime object
            "labels": [label.name for label in issue.labels],
            "assignees": [assignee.login for assignee in issue.assignees],
            "user": issue.user.login if issue.user else None,
            "html_url": issue.html_url,
            "comments": issue.comments,
        }

        client.close()

        return {
            "success": True,
            "message": f"Retrieved issue #{issue_number}",
            "issue": issue_data,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# # PREPARE ISSUE
def _prepare_issue_body_from_contribution(contribution):
    """Prepare the body content for a GitHub issue from provided `contribution`.

    :param contribution: contribution instance to extract data from
    :type contribution: :class:`contributions.models.Contribution`
    :var issue_body: default issue body template
    :type issue_body: str
    :var message: parsed message data from contribution URL
    :type message: dict
    :return: str
    """
    issue_body = "** Please provide the necessary information **"
    if not contribution.url:
        return issue_body

    message = message_from_url(contribution.url)
    if message.get("success"):
        author = message.get("author")
        timestamp = datetime.strptime(
            message.get("timestamp"), "%Y-%m-%dT%H:%M:%S.%f%z"
        ).strftime("%d %b %H:%M")
        issue_body = f"By {author} on {timestamp} in [Discord]({contribution.url}):\n"
        for line in message.get("content").split("\n"):
            issue_body += f"> {line}\n"

    return issue_body


def _prepare_issue_labels_from_contribution(contribution):
    """Prepare labels for a GitHub issue based on contribution reward type.

    :param contribution: contribution instance to extract data from
    :type contribution: :class:`contributions.models.Contribution`
    :var labels: collection of labels to apply to the issue
    :type labels: list
    :return: list
    """
    labels = []
    if "Bug" in contribution.reward.type.name:
        labels.append("bug")

    elif "Feature" in contribution.reward.type.name:
        labels.append("feature")

    elif "Task" in contribution.reward.type.name:
        labels.append("task")

    elif "Twitter" in contribution.reward.type.name:
        labels.append("task")

    elif "Research" in contribution.reward.type.name:
        labels.append("research")

    return labels


def _prepare_issue_priority_from_contribution(contribution):
    """Prepare priority level for a GitHub issue based on contribution reward type.

    :param contribution: contribution instance to extract data from
    :type contribution: :class:`contributions.models.Contribution`
    :return: str
    """
    if "Bug" in contribution.reward.type.name:
        return "high priority"

    return "medium priority"


def _prepare_issue_title_from_contribution(contribution):
    """Prepare title for a GitHub issue from contribution data.

    :param contribution: contribution instance to extract data from
    :type contribution: :class:`contributions.models.Contribution`
    :var issue_title: formatted issue title with reward type and level
    :type issue_title: str
    :return: str
    """
    issue_title = f"[{contribution.reward.type.label}{contribution.reward.level}] "
    if contribution.comment:
        issue_title += contribution.comment

    return issue_title


def issue_data_for_contribution(contribution):
    """Prepare complete issue data dictionary from a contribution.

    :param contribution: contribution instance to extract data from
    :type contribution: :class:`contributions.models.Contribution`
    :return: dict
    """
    return {
        "issue_title": _prepare_issue_title_from_contribution(contribution),
        "issue_body": _prepare_issue_body_from_contribution(contribution),
        "labels": _prepare_issue_labels_from_contribution(contribution),
        "priority": _prepare_issue_priority_from_contribution(contribution),
    }
