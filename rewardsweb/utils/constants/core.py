"""Module containing core app's constants."""

ADDRESS_LEN = 58

MISSING_ENVIRONMENT_VARIABLE_ERROR = "Environment variable is not set"

HANDLE_EXCEPTIONS = ("RR", "Di")

CONTRIBUTIONS_TAIL_SIZE = 5

DISCORD_NOTED_EMOJI = "noted:930825381974523954"
DISCORD_ADDRESSED_EMOJI = "addressed:930825322654470204"
DISCORD_NOTAPPLICABLE_EMOJI = "na:910968758284202015"
DISCORD_EXISTS_EMOJI = "exists:929454747801489438"

ISSUE_CREATION_LABEL_CHOICES = [
    ("feature", "Feature"),
    ("bug", "Bug"),
    ("task", "Task"),
    ("research", "Research"),
    ("mobile", "Mobile"),
    ("work in progress", "Work in progress"),
]

ISSUE_LABEL_CHOICES = ISSUE_CREATION_LABEL_CHOICES + [
    ("wontfix", "Wontfix"),
    ("addressed", "Addressed"),
    ("archived", "Archived"),
]

ISSUE_PRIORITY_CHOICES = [
    ("low priority", "Low Priority"),
    ("medium priority", "Medium Priority"),
    ("high priority", "High Priority"),
]

GITHUB_LABELS = (
    "high priority",
    "medium priority",
    "low priority",
    "feature",
    "bug",
    "task",
    "research",
    "mobile",
    "addressed",
    "archived",
    "wontfix",
)

TOO_LONG_USER_FIRST_NAME_ERROR = "User name is limited to 30 characters only"
TOO_LONG_USER_LAST_NAME_ERROR = "User last name is limited to 150 characters only"
