"""Module containing helper functions for GitHub issues mapping."""

import re

from django.conf import settings
from django.db import transaction

from core.models import Contribution, Issue, IssueStatus
from utils.issues import fetch_issues


def _create_issues_bulk(issue_assignments):
    """Bulk create issues and assign them to contributions in optimized database operations.

    This function processes issue-contribution assignments in bulk to minimize
    database round-trips. It creates missing issues and updates contributions
    with their assigned issues using bulk operations.

    :param issue_assignments: list of issue number and contribution ID pairs to assign
    :type issue_assignments: list of tuple (int, int)
    :var unique_issue_numbers: set of distinct GitHub issue numbers to process
    :type unique_issue_numbers: set of int
    :var existing_issues: existing Issue objects from database
    :type existing_issues: QuerySet of :class:`core.models.Issue`
    :var existing_issue_numbers: set of issue numbers that already exist in database
    :type existing_issue_numbers: set of int
    :var issues_to_create: list of Issue instances to create in bulk
    :type issues_to_create: list of :class:`core.models.Issue`
    :var fetch_issues_dict: mapping from issue number to Issue instance
    :type fetch_issues_dict: dict of int: :class:`core.models.Issue`
    :var contribution_updates: list of contribution ID and Issue instance pairs
    :type contribution_updates: list of tuple (int, :class:`core.models.Issue`)
    :var contribution_ids: list of contribution IDs to update
    :type contribution_ids: list of int
    :var contributions: Contribution objects to be updated
    :type contributions: QuerySet of :class:`core.models.Contribution`
    :var issue_by_contribution_id: mapping from contribution ID to assigned Issue
    :type issue_by_contribution_id: dict of int: :class:`core.models.Issue`
    """
    if not issue_assignments:
        return

    # Get unique issue numbers
    unique_issue_numbers = {number for number, _ in issue_assignments}

    # Get existing issues
    existing_issues = Issue.objects.filter(number__in=unique_issue_numbers)
    existing_issue_numbers = set(existing_issues.values_list("number", flat=True))

    # Create missing issues
    issues_to_create = [
        Issue(number=number, status=IssueStatus.ARCHIVED)
        for number in unique_issue_numbers
        if number not in existing_issue_numbers
    ]

    if issues_to_create:
        Issue.objects.bulk_create(issues_to_create)

    # Get all issues (newly created + existing)
    fetch_issues_dict = {
        issue.number: issue
        for issue in Issue.objects.filter(number__in=unique_issue_numbers)
    }

    # Prepare contribution updates
    contribution_updates = []
    for issue_number, contribution_id in issue_assignments:
        if issue_number in fetch_issues_dict:
            contribution_updates.append(
                (contribution_id, fetch_issues_dict[issue_number])
            )

    # Bulk update contributions
    if contribution_updates:
        contribution_ids = [cont_id for cont_id, _ in contribution_updates]
        contributions = Contribution.objects.filter(id__in=contribution_ids)

        # Create mapping for updates
        issue_by_contribution_id = {
            cont_id: issue for cont_id, issue in contribution_updates
        }

        # Update in bulk
        for contribution in contributions:
            contribution.issue = issue_by_contribution_id[contribution.id]

        Contribution.objects.bulk_update(contributions, ["issue"])


@transaction.atomic
def _fetch_and_assign_closed_issues(github_token):
    """Fetch GitHub issues and assign them to contributions based on URL matching.

    This function retrieves all closed GitHub issues and attempts to match them with
    existing contributions by searching for contribution URLs in the issue bodies.
    When a match is found, creates an Issue record and assigns it to the contribution.

    :param github_token: GitHub authentication token
    :type github_token: str
    :var contributions: all the existing contribution instances
    :type contributions: QuerySet of :class:`core.models.Contribution`
    :var url_to_contribution: mapping from URL to contribution instance
    :type url_to_contribution: dict of str: :class:`core.models.Contribution`
    :var github_issues: list of GitHub issue instances retrieved from API
    :type github_issues: list of :class:`github.Issue.Issue`
    :var issue_assignments: collection of issue number and contribution ID pairs to process
    :type issue_assignments: set of tuple (int, int)
    :return: True if operation completed successfully, False if no token provided
    :rtype: bool
    """
    if not github_token:
        return False

    # Get all contributions in one query
    contributions = Contribution.objects.all().only("id", "url")
    if not contributions:
        return True

    # Get all closed GitHub issues
    github_issues = list(fetch_issues(github_token, state="closed"))

    # Create a mapping from GitHub issue number to issue object for quick lookup
    github_issues_by_number = {issue.number: issue for issue in github_issues}

    # Collect all assignments in memory first
    issue_assignments = set()

    # Process each contribution and try to find matching GitHub issues
    for contribution in contributions:
        if not contribution.url:
            continue

        # Method 1: Check if contribution URL is a GitHub issue URL
        issue_number = _is_url_github_issue(contribution.url)
        if issue_number and issue_number in github_issues_by_number:
            # This contribution URL points directly to a GitHub issue
            issue_assignments.add((issue_number, contribution.id))
            continue  # Skip body matching if we found a direct GitHub issue match

        # Method 2: Search through all GitHub issues for this contribution's URL in their bodies
        for github_issue in github_issues:
            if (
                github_issue.body
                and contribution.url
                and contribution.url in github_issue.body
            ):
                issue_assignments.add((github_issue.number, contribution.id))
                break  # One issue per contribution (first match found)

    # Process all assignments in bulk
    _create_issues_bulk(list(issue_assignments))

    return True


def _is_url_github_issue(url):
    """Check if a URL matches the pattern of a GitHub issue in the configured repository.

    :param url: URL to check
    :type url: str
    :return: GitHub issue number if URL matches pattern, False otherwise
    :rtype: int or bool
    :var pattern: regex pattern for GitHub issue URL matching
    :type pattern: str
    :var match: regex match object
    :type match: :class:`re.Match` or None
    """
    pattern = (
        rf"^.*github\.com/{settings.GITHUB_REPO_OWNER}/"
        rf"{settings.GITHUB_REPO_NAME}/issues/(\d+).*"
    )
    match = re.match(pattern, url)
    if not match:
        return False

    return int(match.groups()[0])


def map_github_issues(github_token=""):
    """Import contributions from CSV files to database.

    :param github_token: GitHub API token
    :type github_token: str
    :return: Error message string or False if successful
    :rtype: str or bool
    """
    _fetch_and_assign_closed_issues(github_token)
    # _fetch_and_assign_open_issues(github_token)

    print("Issues created: ", len(Issue.objects.all()))
    return False
