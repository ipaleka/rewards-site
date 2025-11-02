"""Module containing functions for GitHub issues management."""

import logging
from datetime import datetime, timedelta

import jwt
import requests
from django.conf import settings
from github import Auth, Github

from core.models import Contributor
from utils.bot import message_from_url
from utils.constants.core import GITHUB_ISSUES_START_DATE
from utils.constants.ui import MISSING_TOKEN_TEXT
from utils.helpers import get_env_variable

logger = logging.getLogger(__name__)


class GitHubApp:
    """Helper class for instantiating GitHub client using GitHub bot."""

    def jwt_token(self):
        """Generate JWT token for GitHub bot.

        :var bot_private_key_filename: filename of the bot's private key
        :type bot_private_key_filename: str
        :var bot_client_id: client ID of the bot
        :type bot_client_id: str
        :var pem_path: path to the bot's private key
        :type pem_path: :class:`pathlib.Path`
        :var signing_key: bot's private key
        :type signing_key: bytes
        :var now: current time
        :type now: :class:`datetime.datetime`
        :var expiration: expiration time for the token
        :type expiration: :class:`datetime.datetime`
        :var payload: JWT payload
        :type payload: dict
        :return: JWT token
        :rtype: str
        """
        bot_private_key_filename = get_env_variable(
            "GITHUB_BOT_PRIVATE_KEY_FILENAME", ""
        )
        bot_client_id = get_env_variable("GITHUB_BOT_CLIENT_ID", "")
        if not (bot_private_key_filename and bot_client_id):
            return None

        pem_path = settings.BASE_DIR.parent / "fixtures" / bot_private_key_filename
        with open(pem_path, "rb") as pem_file:
            signing_key = pem_file.read()

        now = datetime.now()
        expiration = now + timedelta(minutes=8)
        payload = {
            "iat": int(now.timestamp()),
            "exp": int(expiration.timestamp()),
            "iss": bot_client_id,
        }
        return jwt.encode(payload, signing_key, algorithm="RS256")

    def installation_token(self):
        """Retrieve installation access token for GitHub bot.

        :var installation_id: ID of the bot's installation
        :type installation_id: str
        :var jwt_token: JWT token for the bot
        :type jwt_token: str
        :var headers: headers for the request
        :type headers: dict
        :var url: URL for the request
        :type url: str
        :var response: response from the request
        :type response: :class:`requests.Response`
        :return: installation access token
        :rtype: str
        """
        installation_id = get_env_variable("GITHUB_BOT_INSTALLATION_ID", "")
        if not installation_id:
            return None

        jwt_token = self.jwt_token()
        if not jwt_token:
            return None

        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        url = (
            f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        )
        response = requests.post(url, headers=headers)
        return response.json().get("token") if response.status_code == 201 else None

    def client(self):
        """Get authenticated GitHub client using GitHub bot.

        :var token: installation access token
        :type token: str
        :return: authenticated GitHub client
        :rtype: :class:`github.Github`
        """
        token = self.installation_token()
        return Github(token) if token else None


# # HELPERS
def _contributor_link(handle):
    """Create link to contributor defined by provided Discord `handle`.

    :param handle: Discord handle/username
    :type handle: str
    :param contributor: contributor's model instance
    :type contributor: :class:`core.models.Contributor`
    :return: str
    """
    try:
        contributor = Contributor.objects.from_handle(handle)

    except ValueError:
        contributor = None

    if contributor is None:
        return handle

    return f"[{handle}]({contributor.get_absolute_url()})"


# # CRUD
def _github_client(user):
    """Instantiate and return GitHub client instance on behalf GitHub bot or `user`.

    :param user: Django user instance
    :type user: class:`django.contrib.auth.models.User`
    :var client: GitHub client instance
    :type client: :class:`github.Github`
    :var auth: GitHub authentication token instance
    :type auth: :class:`github.Github`
    :return: :class:`github.Github`
    """
    client = GitHubApp().client()
    if client:
        return client

    if not user.profile.github_token:
        return False

    auth = Auth.Token(user.profile.github_token)
    return Github(auth=auth)


def _github_repository(client):
    """Return instance of GitHub repository holding project's issues.

    :param client: GitHub client instance
    :type client: :class:`github.Github`
    :return: :class:`github.Repository.Repository`
    """
    return client.get_repo(f"{settings.GITHUB_REPO_OWNER}/{settings.GITHUB_REPO_NAME}")


def fetch_issues(github_token, state="all", since=GITHUB_ISSUES_START_DATE):
    """Fetch all GitHub issues with provided `state` from the configured repository.

    :param github_token: GitHub authentication token
    :type github_token: str
    :param since: fetch only issues that have been updated after this date
    :type since: :class:`datetime.datetime`
    :var auth: GitHub authentication instance
    :type auth: :class:`github.Auth.Token`
    :var client: GitHub client instance
    :type client: :class:`github.Github`
    :var repo: GitHub repository instance
    :type repo: :class:`github.Repository.Repository`
    :var issues: collection of GitHub issue instances
    :type issues: list
    :return: collection of GitHub issues
    :rtype: :class:`github.PaginatedList`
    """
    auth = Auth.Token(github_token)
    client = Github(auth=auth)
    if not client:
        return []

    repo = _github_repository(client)
    issues = repo.get_issues(state=state, sort="updated", direction="asc", since=since)

    return issues


def close_issue_with_labels(user, issue_number, labels_to_set=None, comment=None):
    """Close GitHub issue defined by `issue_number` on behalf `user`.

    :param user: Django user instance
    :type user: class:`django.contrib.auth.models.User`
    :param issue_number: unique issue's number
    :type issue_number: int
    :param body: formatted issue's body text
    :type body: str
    :param labels_to_set: collection of GitHub labels to set to the issue
    :type labels_to_set: list
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
        if labels_to_set:
            issue.set_labels(*labels_to_set)

        # Add comment if provided
        if comment:
            issue.create_comment(comment)

        # Close the issue
        issue.edit(state="closed")

        client.close()

        return {
            "success": True,
            "message": f"Closed issue #{issue_number} with labels {labels_to_set}",
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
            "created_at": issue.created_at,
            "updated_at": issue.updated_at,
            "closed_at": issue.closed_at,
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


def set_labels_to_issue(user, issue_number, labels_to_set):
    """Add provided `labels` to the issue defined by `issue_number` on behalf `user`.

    :param user: Django user instance
    :type user: class:`django.contrib.auth.models.User`
    :param issue_number: unique issue's number
    :type issue_number: int
    :param labels_to_set: collection of GitHub labels to add to the issue
    :type labels_to_set: list
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
        issue.set_labels(*labels_to_set)

        client.close()

        return {
            "success": True,
            "message": f"Added labels {labels_to_set} to issue #{issue_number}",
            "current_labels": [label.name for label in issue.labels],
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# # PREPARE ISSUE
def _prepare_issue_body_from_contribution(contribution, profile):
    """Prepare the body content for a GitHub issue from provided arguments.

    :param contribution: contribution instance to extract data from
    :type contribution: :class:`core.models.Contribution`
    :param profile: superuser's profile instance
    :type profile: :class:`core.models.Profile`
    :var issue_body: default issue body template
    :type issue_body: str
    :var message: parsed message data from contribution URL
    :type message: dict
    :var contributor: link to contributor's page on rewards website
    :type contributor: str
    :return: str
    """
    issue_body = "** Please provide the necessary information **"
    if not contribution.url:
        return issue_body

    message = message_from_url(contribution.url)
    if message.get("success"):
        timestamp = datetime.strptime(
            message.get("timestamp"), "%Y-%m-%dT%H:%M:%S.%f%z"
        ).strftime("%d %b %H:%M")
        contributor = _contributor_link(message.get("author"))
        issue_body = (
            f"By {contributor} on {timestamp} in [Discord]"
            f"({contribution.url}): // su: {str(profile)}\n"
        )
        for line in message.get("content").split("\n"):
            issue_body += f"> {line}\n"

    return issue_body


def _prepare_issue_labels_from_contribution(contribution):
    """Prepare labels for a GitHub issue based on contribution reward type.

    :param contribution: contribution instance to extract data from
    :type contribution: :class:`core.models.Contribution`
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
    :type contribution: :class:`core.models.Contribution`
    :return: str
    """
    if "Bug" in contribution.reward.type.name:
        return "high priority"

    return "medium priority"


def _prepare_issue_title_from_contribution(contribution):
    """Prepare title for a GitHub issue from contribution data.

    :param contribution: contribution instance to extract data from
    :type contribution: :class:`core.models.Contribution`
    :var issue_title: formatted issue title with reward type and level
    :type issue_title: str
    :return: str
    """
    issue_title = f"[{contribution.reward.type.label}{contribution.reward.level}] "
    if contribution.comment:
        issue_title += contribution.comment

    return issue_title


def issue_data_for_contribution(contribution, profile):
    """Prepare complete issue data dictionary from a contribution.

    :param contribution: contribution instance to extract data from
    :type contribution: :class:`core.models.Contribution`
    :param profile: superuser's profile instance
    :type profile: :class:`core.models.Profile`
    :return: dict
    """
    return {
        "issue_title": _prepare_issue_title_from_contribution(contribution),
        "issue_body": _prepare_issue_body_from_contribution(contribution, profile),
        "labels": _prepare_issue_labels_from_contribution(contribution),
        "priority": _prepare_issue_priority_from_contribution(contribution),
    }
