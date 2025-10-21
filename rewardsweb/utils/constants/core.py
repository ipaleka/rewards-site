"""Module containing core app's constants."""

ADDRESS_LEN = 58

MISSING_ENVIRONMENT_VARIABLE_ERROR = "Environment variable is not set"

HANDLE_EXCEPTIONS = ("RR", "Di")

CONTRIBUTIONS_TAIL_SIZE = 5

DISCORD_EMOJIS = {
    "noted": "noted:930825381974523954",
    "addressed": "addressed:930825322654470204",
    "wontfix": "noted:910968758284202015",
    "duplicate": "exists:929454747801489438",
}

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
