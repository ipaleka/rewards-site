"""Module containing projects' helper functions."""

import logging
import os

from django.core.exceptions import ImproperlyConfigured

from utils.constants.core import MISSING_ENVIRONMENT_VARIABLE_ERROR

logger = logging.getLogger(__name__)


def get_env_variable(name, default=None):
    """Return environment variable with provided `name`.

    Raise `ImproperlyConfigured` exception if such variable isn't set.

    :param name: name of environment variable
    :type name: str
    :param default: environment variable's default value
    :type default: str
    :return: str
    """
    try:
        return os.environ[name]
    except KeyError:
        if default is None:
            raise ImproperlyConfigured(
                "{} {}!".format(name, MISSING_ENVIRONMENT_VARIABLE_ERROR)
            )
        return default


def humanize_contributions(contributions):
    """Return collection of provided `contributions` formatted for output.

    TODO: tests

    :param contributions: collectin of users' contribution instances
    :type contributions: :class:`django.db.models.query.QuerySet`
    :return: list
    """
    return [
        {
            "id": c.id,
            "contributor_name": c.contributor.name,
            "cycle_id": c.cycle.id,
            "platform": c.platform.name,
            "url": c.url,
            "type": c.reward.type,
            "level": c.reward.level,
            "percentage": c.percentage,
            "reward": c.reward.amount,
            "confirmed": c.confirmed,
        }
        for c in contributions
    ]
