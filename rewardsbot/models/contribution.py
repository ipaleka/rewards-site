class Contribution:
    def __init__(self, data):
        self.id = data.get("id")
        self.contributor_name = data.get("contributor_name")
        self.cycle_id = data.get("cycle_id")
        self.platform = data.get("platform")
        self.url = data.get("url")
        self.type = data.get("type")
        self.level = data.get("level")
        self.percentage = data.get("percentage")
        self.reward = data.get("reward")
        self.confirmed = data.get("confirmed")

    def format(self, is_user_summary=False):
        import re

        type_short = re.search(r"\[(.*?)\]", self.type)
        type_short = type_short.group(1) if type_short else self.type

        reward = float(self.reward) if self.reward else 0.0

        if is_user_summary:
            return f"[[{type_short}{self.level}]]({self.url}) {reward:.2f} damo"
        return f"[{self.contributor_name} [{type_short}{self.level}]]({self.url}) {reward:.2f} damo"
