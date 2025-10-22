"""Module containing helper functions for importing contributions to database."""

import re
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.utils import IntegrityError
from django.http import Http404
from django.shortcuts import get_object_or_404

from core.models import (
    Contributor,
    Contribution,
    Cycle,
    Handle,
    Issue,
    IssueStatus,
    Reward,
    RewardType,
    SocialPlatform,
)
from utils.helpers import get_env_variable
from utils.issues import fetch_issues


ADDRESSES_CSV_COLUMNS = ["handle", "address"]
CONTRIBUTION_CSV_COLUMNS = [
    "contributor",
    "cycle_start",
    "cycle_end",
    "platform",
    "url",
    "type",
    "level",
    "percentage",
    "reward",
    "comment",
]
REWARDS_COLLECTION = (
    ("[F] Feature Request", 30000, 60000, 135000),
    ("[B] Bug Report", 30000, 60000, 135000),
    ("[AT] Admin Task", 35000, 70000, 150000),
    ("[CT] Content Task", 100000, 200000, 300000),
    ("[IC] Issue Creation", 30000, 60000, 135000),
    ("[TWR] Twitter Post", 30000, 60000, 135000),
    ("[D] Development", 100000, 200000, 300000),
    ("[ER] Ecosystem Research", 50000, 100000, 200000),
)


def _check_current_cycle(cycle_instance):
    """Check if current cycle has ended and create new cycle if needed.

    :param cycle_instance: The latest cycle instance to check
    :type cycle_instance: :class:`core.models.Cycle`
    """
    if datetime.now().date() > cycle_instance.end:
        start = cycle_instance.end + timedelta(days=1)
        end = start + timedelta(days=92)
        end = datetime(end.year, end.month, 1) + timedelta(days=-1)
        Cycle.objects.create(start=start, end=end)


def _create_active_rewards():
    """Create or activate reward objects based on REWARDS_COLLECTION."""
    for index in range(len(REWARDS_COLLECTION)):
        reward = REWARDS_COLLECTION[index]
        reward_name = reward[0]
        for level, amount in enumerate(reward):
            if level == 0:
                continue

            label, name = (
                reward_name.split(" ", 1)[0].strip("[]"),
                reward_name.split(" ", 1)[1].strip(),
            )
            reward_type = get_object_or_404(RewardType, label=label, name=name)
            try:
                reward = Reward.objects.get(
                    type=reward_type, level=level, amount=amount
                )
                reward.active = True
                reward.save()

            except ObjectDoesNotExist:
                Reward.objects.create(
                    type=reward_type, level=level, amount=amount, active=True
                )


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


def _create_superusers():
    """Create initial superusers from environment variables."""
    superusers = get_env_variable("INITIAL_SUPERUSERS", "").split(",")
    passwords = get_env_variable("DEFAULT_USER_PASSWORD", "").split(",")
    assert len(superusers) == len(passwords)
    for index, superuser in enumerate(superusers):
        User.objects.create_superuser(superuser, password=passwords[index])


def _dataframe_from_csv(filename, columns=CONTRIBUTION_CSV_COLUMNS):
    """Create pandas DataFrame from CSV file.

    :param filename: Path to the CSV file
    :type filename: str
    :param columns: List of column names for the DataFrame
    :type columns: list
    :return: DataFrame with specified columns or None if file not found/empty
    :rtype: :class:`pandas.DataFrame` or None
    """
    try:
        data = pd.read_csv(filename, header=None, sep=",")
    except (pd.errors.EmptyDataError, FileNotFoundError):
        return None
    data.columns = columns
    return data


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


def _import_contributions(data, parse_callback, amount_callback):
    """Import contributions from DataFrame to database.

    :param data: DataFrame containing contribution data
    :type data: :class:`pandas.DataFrame`
    :param parse_callback: Function to parse reward type from string
    :type parse_callback: callable
    :param amount_callback: Function to calculate reward amount
    :type amount_callback: callable
    """
    for _, row in data.iterrows():
        contributor = Contributor.objects.from_full_handle(row["contributor"])
        cycle = Cycle.objects.get(start=row["cycle_start"])
        platform = SocialPlatform.objects.get(name__iexact=row["platform"])
        label, name = parse_callback(row["type"])
        reward_type = get_object_or_404(RewardType, label=label, name=name)
        reward = Reward.objects.get(
            type=reward_type,
            level=row["level"] if not pd.isna(row["level"]) else 1,
            amount=amount_callback(row["reward"]),
        )
        percentage = row["percentage"] if not pd.isna(row["percentage"]) else 1
        url = row["url"] if not pd.isna(row["url"]) else None
        comment = row["comment"] if not pd.isna(row["comment"]) else None
        Contribution.objects.create(
            contributor=contributor,
            cycle=cycle,
            platform=platform,
            reward=reward,
            percentage=percentage,
            url=url,
            comment=comment,
            confirmed=True,
        )


def _import_rewards(data, parse_callback, amount_callback):
    """Import rewards from DataFrame to database.

    :param data: DataFrame containing reward data
    :type data: :class:`pandas.DataFrame`
    :param parse_callback: Function to parse reward type from string
    :type parse_callback: callable
    :param amount_callback: Function to calculate reward amount
    :type amount_callback: callable
    """
    for typ, level, reward in data.values.tolist():
        label, name = parse_callback(typ)
        try:
            reward_type = get_object_or_404(RewardType, label=label, name=name)

        except Http404:
            reward_type = RewardType.objects.create(label=label, name=name)

        try:
            Reward.objects.create(
                type=reward_type,
                level=level if not pd.isna(level) else 1,
                amount=amount_callback(reward),
                active=False,
            )
        except IntegrityError:
            pass


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


def _parse_addresses():
    """Parse addresses from CSV file and group by address.

    :return: List of addresses with associated handles
    :rtype: list
    """
    addresses_filename = (
        Path(__file__).resolve().parent.parent / "fixtures" / "addresses.csv"
    )
    data = _dataframe_from_csv(addresses_filename, columns=ADDRESSES_CSV_COLUMNS)
    if data is None:
        return []

    data = data[["handle", "address"]].drop_duplicates()
    grouped = (
        data.groupby("address")["handle"]
        .apply(lambda x: x.tolist()[::-1])
        .reset_index()
    )
    return grouped.values.tolist()


def _parse_label_and_name_from_reward_type_legacy(typ):
    """Parse reward type label and name from legacy format.

    :param typ: Reward type string in legacy format
    :type typ: str
    :return: Tuple of (label, name)
    :rtype: tuple
    """
    label, name = _parse_label_and_name_from_reward_type(typ)
    if name == "Custom":
        if "feature request" in typ:
            return "F", "Feature Request"

        if "bug report" in typ:
            return "B", "Bug Report"

        if "ecosystem research" in typ:
            return "ER", "Ecosystem Research"

        return "S", "Suggestion"

    return label, name


def _parse_label_and_name_from_reward_type(typ):
    """Parse reward type label and name from standard format.

    :param typ: Reward type string in format "[LABEL] Name"
    :type typ: str
    :return: Tuple of (label, name)
    :rtype: tuple
    """
    if not pd.isna(typ):
        pattern = r"\[([^\]]+)\]\s*(.+)"
        match = re.match(pattern, typ)
        if match:
            return match.group(1), match.group(2)

    return "CST", "Custom"


def _reward_amount(reward):
    """Calculate reward amount in base units.

    :param reward: Reward amount
    :type reward: float
    :return: Reward amount in base units
    :rtype: int
    """
    return round(reward * 1_000_000) if not pd.isna(reward) else 0


def _reward_amount_legacy(reward):
    """Calculate legacy reward amount in base units.

    :param reward: Reward amount
    :type reward: float
    :return: Reward amount in base units
    :rtype: int
    """
    return round(round(reward, 2) * 1_000_000) if not pd.isna(reward) else 0


def _social_platforms():
    """Return list of social platforms with their prefixes.

    :return: List of tuples (platform_name, prefix)
    :rtype: list
    """
    return [
        ("Discord", ""),
        ("Twitter", "@"),
        ("Reddit", "u/"),
        ("GitHub", "g@"),
        ("Telegram", "t@"),
        ("Forum", "f@"),
    ]


def convert_and_clean_excel(input_file, output_file, legacy_contributions):
    """Convert and clean Excel file to CSV format for import.

    :param input_file: Path to input Excel file
    :type input_file: str
    :param output_file: Path to output CSV file for current contributions
    :type output_file: str
    :param legacy_contributions: Path to output CSV file for legacy contributions
    :type legacy_contributions: str
    """
    df = pd.read_excel(input_file, sheet_name=3, header=None).iloc[2:]

    with pd.option_context("future.no_silent_downcasting", True):
        df = df.fillna("NULL").infer_objects(copy=False)

    df.drop(columns=[4, 11, 12, 13, 14, 15, 16], inplace=True)

    df = df[~df[0].str.startswith("Period below")]

    df = df.map(lambda x: str(x).replace(" 00:00:00", ""))

    df.loc[df[1] == "45276", 1] = "2023-12-16"
    df.loc[df[2] == "45303", 2] = "2024-01-12"
    df.loc[df[2] == "Legal entity research", 6] = "[AT] Admin Task"
    df.loc[df[2] == "Legal entity research", 2] = "NULL"
    df.loc[df[1] == "NULL", 1] = (
        "2021-12-10"  # Legal entity, add date (assign to cycle)
    )
    df.loc[df[2] == "NULL", 2] = (
        "2021-12-31"  # Legal entity, add date (assign to cycle)
    )

    df = df[~df[0].str.startswith("NULL")]  # Clean rows where first column is 'NULL'

    # in this part we are moving a historic cycle appended at the end of the file to where it should be, chronologically
    MOVED_CYCLE_LENGTH = 66  # constant length of the historic cycle
    df_len = len(df.index) - 1

    replacement_index = df_len - MOVED_CYCLE_LENGTH

    print("DF length: " + str(len(df.index)))

    df1 = df.iloc[:855]  # start part
    df2 = df.iloc[replacement_index:]  # Part to cut and insert
    df3 = df.iloc[855:replacement_index]  # final part

    df = pd.concat([df1, df2, df3])
    df[0] = df[0].str.strip()  # Remove leading and trailing spaces from column 0

    # full csv export for debugging
    path = Path(__file__).resolve().parent.parent / "fixtures" / "fullcsv.csv"
    df.to_csv(path, index=False, header=None, na_rep="NULL")

    # FINAL EXPORT

    legacy_df = df.iloc[:82]
    df = df.iloc[82:]

    df.to_csv(output_file, index=False, header=None, na_rep="NULL")
    legacy_df.to_csv(legacy_contributions, index=False, header=None, na_rep="NULL")


def import_from_csv(contributions_path, legacy_contributions_path, github_token=""):
    """Import contributions from CSV files to database.

    :param contributions_path: Path to current contributions CSV file
    :type contributions_path: str
    :param legacy_contributions_path: Path to legacy contributions CSV file
    :type legacy_contributions_path: str
    :param github_token: GitHub API token
    :type github_token: str
    :return: Error message string or False if successful
    :rtype: str or bool
    """
    # # CHECK
    if len(SocialPlatform.objects.all()):
        return "ERROR: Database is not empty!"

    # # PLATFORMS
    SocialPlatform.objects.bulk_create(
        SocialPlatform(name=name, prefix=prefix) for name, prefix in _social_platforms()
    )
    print("Social platforms created: ", len(SocialPlatform.objects.all()))

    # # ADDRESSES
    addresses = _parse_addresses()
    Contributor.objects.bulk_create(
        Contributor(name=handles[0], address=address) for address, handles in addresses
    )
    print("Contributors imported: ", len(Contributor.objects.all()))
    for address, handles in addresses:
        for full_handle in handles:
            handle = Handle.objects.from_address_and_full_handle(address, full_handle)
            handle.save()
    print("Handles imported: ", len(Handle.objects.all()))

    # # CONTRIBUTIONS
    data = _dataframe_from_csv(contributions_path)
    legacy_data = _dataframe_from_csv(legacy_contributions_path)

    cycles_data = data[["cycle_start", "cycle_end"]].drop_duplicates()
    legacy_cycles_data = legacy_data[["cycle_start", "cycle_end"]].drop_duplicates()
    all_cycles_data = pd.concat([cycles_data, legacy_cycles_data]).sort_values(
        by=["cycle_start"]
    )
    Cycle.objects.bulk_create(
        Cycle(start=start, end=end) for start, end in all_cycles_data.values.tolist()
    )
    _check_current_cycle(Cycle.objects.latest("end"))
    print("Cycles imported: ", len(Cycle.objects.all()))

    _import_rewards(
        data[["type", "level", "reward"]],
        _parse_label_and_name_from_reward_type,
        _reward_amount,
    )
    _import_rewards(
        legacy_data[["type", "level", "reward"]],
        _parse_label_and_name_from_reward_type_legacy,
        _reward_amount_legacy,
    )
    _create_active_rewards()
    print("Rewards imported: ", len(Reward.objects.all()))

    _import_contributions(
        legacy_data,
        _parse_label_and_name_from_reward_type_legacy,
        _reward_amount_legacy,
    )
    _import_contributions(
        data,
        _parse_label_and_name_from_reward_type,
        _reward_amount,
    )
    print("Contributions imported: ", len(Contribution.objects.all()))

    _fetch_and_assign_closed_issues(github_token)
    print("Issues created: ", len(Issue.objects.all()))

    _create_superusers()

    return False
