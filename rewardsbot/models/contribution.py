import re


def _create_link(linktext, url):
    if url:
        return f"[{linktext}]({url})"

    return f"{linktext}"


class Contribution:
    def __init__(self, data):
        self.id = data.get("id")
        self.contributor_name = data.get("contributor_name")
        self.cycle_id = data.get("cycle")
        self.platform = data.get("platform")
        self.url = data.get("url")
        self.type = data.get("type")
        self.level = data.get("level")
        self.percentage = data.get("percentage")
        self.reward = data.get("reward")
        self.confirmed = data.get("confirmed")

    def formatted_contributions(self, is_user_summary=False):
        type_short = re.search(r"\[(.*?)\]", self.type)
        type_short = type_short.group(1) if type_short else self.type
        reward = self.reward or 0
        linktext = (
            f"{type_short}{self.level}"
            if is_user_summary
            else f"{self.contributor_name} [{type_short}{self.level}]"
        )
        link = _create_link(linktext, self.url)

        return f"{link} {reward:,}"
