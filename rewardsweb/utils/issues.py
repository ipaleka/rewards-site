"""Module containing functions for GitHub issues management."""

import logging

from django.conf import settings
from github import Auth, Github

logger = logging.getLogger(__name__)


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


def create_github_issue(user, title, body, labels=None):
    """Create GitHub issue on behalf `user` defined by provided arguments .

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
