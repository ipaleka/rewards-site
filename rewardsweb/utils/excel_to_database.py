"""Module containing helper functions for importing contributions to database."""

import re
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from django.db.utils import IntegrityError
from django.http import Http404
from django.shortcuts import get_object_or_404

from core.models import (
    Contributor,
    Contribution,
    Cycle,
    Handle,
    Reward,
    RewardType,
    SocialPlatform,
)


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


def _check_current_cycle(cycle_instance):
    if datetime.now().date() > cycle_instance.end:
        start = cycle_instance.end + timedelta(days=1)
        end = start + timedelta(days=92)
        end = datetime(end.year, end.month, 1) + timedelta(days=-1)
        Cycle.objects.create(start=start, end=end)


def _dataframe_from_csv(filename, columns=CONTRIBUTION_CSV_COLUMNS):
    try:
        data = pd.read_csv(filename, header=None, sep=",")
    except (pd.errors.EmptyDataError, FileNotFoundError):
        return None
    data.columns = columns
    return data


def _import_contributions(data, parse_callback, amount_callback):
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
        )


def _import_rewards(data, parse_callback, amount_callback):
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
            )
        except IntegrityError:
            pass


def _parse_addresses():
    addresses_filename = (
        Path(__file__).resolve().parent.parent / "fixtures" / "addresses.csv"
    )
    data = _dataframe_from_csv(addresses_filename, columns=ADDRESSES_CSV_COLUMNS)
    data = data[["handle", "address"]].drop_duplicates()
    grouped = (
        data.groupby("address")["handle"]
        .apply(lambda x: x.tolist()[::-1])
        .reset_index()
    )
    return grouped.values.tolist()


def _parse_label_and_name_from_reward_type_legacy(typ):
    label, name = _parse_label_and_name_from_reward_type(typ)
    if name == "Custom":
        if "feature request" in typ:
            return "F", "Feature Request"

        if "bug report" in typ:
            return "B", "Bug Report"

        if "ecosystem research" in typ:
            return "ER", "Ecosystem Research"

        if "suggestion" in typ:
            return "S", "Suggestion"

    return label, name


def _parse_label_and_name_from_reward_type(typ):
    if not pd.isna(typ):
        pattern = r"\[([^\]]+)\]\s*(.+)"
        match = re.match(pattern, typ)
        if match:
            return match.group(1), match.group(2)

    return "CST", "Custom"


def _reward_amount(reward):
    return round(reward * 1_000_000) if not pd.isna(reward) else 0


def _reward_amount_legacy(reward):
    return round(round(reward, 2) * 1_000_000) if not pd.isna(reward) else 0


def _social_platforms():
    return [
        ("Discord", ""),
        ("Twitter", "@"),
        ("Reddit", "u/"),
        ("GitHub", "g@"),
        ("Telegram", "t@"),
        ("Forum", "f@"),
    ]


def convert_and_clean_excel(input_file, output_file, legacy_contributions):
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


def import_from_csv(contributions_path, legacy_contributions_path):
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
        if address == "SIMAHQAOASVV4ORQOOXL3RAQ7KJUGXFDMWMUOAZ5VIAZD2XVMGCZWI45KM":
            pass
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

    return False
