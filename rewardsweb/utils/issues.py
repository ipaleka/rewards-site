"""Module containing functions for GitHub issues management."""

import logging
from datetime import datetime

from django.conf import settings
from github import Auth, Github

from utils.bot import message_from_url

logger = logging.getLogger(__name__)


# # GITHUB
def _github_client(user):
    """Instantiate and return GitHub client instance on behalf `user`.

    :param user: Django user instance
    :type user: class:`django.contrib.auth.models.User`
    :var github_access_token: GitHub user's access token
    :type github_access_token: str
    :var auth: GitHub authentication token instance
    :type auth: :class:`github.Github`
    :return: :class:`github.Github
    """
    github_access_token = user.profile.github_access_token
    if not github_access_token:
        return False

    auth = Auth.Token(github_access_token)

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
            return {
                "success": False,
                "error": "Please provide a GitHub access token in your profile page!",
            }

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
            return {
                "success": False,
                "error": "Please provide a GitHub access token in your profile page!",
            }

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
            return {
                "success": False,
                "error": "Please provide a GitHub access token in your profile page!",
            }

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


# # PREPARE ISSUE
def _prepare_issue_body_from_contribution(contribution):
    """TODO: implement, docstring, and tests"""
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
    """TODO: implement, docstring, and tests"""
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
    """TODO: implement, docstring, and tests"""
    if "Bug" in contribution.reward.type.name:
        return "high priority"

    return "medium priority"


def _prepare_issue_title_from_contribution(contribution):
    """TODO: implement, docstring, and tests"""
    issue_title = f"[{contribution.reward.type.label}{contribution.reward.level}] "
    if contribution.comment:
        issue_title += contribution.comment

    return issue_title


def issue_data_for_contribution(contribution):
    """TODO: implement, docstring, and tests"""

    return {
        "issue_title": _prepare_issue_title_from_contribution(contribution),
        "issue_body": _prepare_issue_body_from_contribution(contribution),
        "labels": _prepare_issue_labels_from_contribution(contribution),
        "priority": _prepare_issue_priority_from_contribution(contribution),
    }
