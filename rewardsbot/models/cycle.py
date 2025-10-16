from datetime import datetime


class Cycle:
    def __init__(self, data):
        self.id = data.get("id")
        self.start = datetime.fromisoformat(data.get("start"))
        self.end = datetime.fromisoformat(data.get("end"))
        self.contributor_rewards = data.get("contributor_rewards", {})
        self.total_rewards = data.get("total_rewards", 0)

    def formatted_cycle_info(self, current=True):
        rewards_info = "\n".join(
            f"{name} {reward:,}" for name, reward in self.contributor_rewards.items()
        )
        prefix, suffix = ("current ", "s") if current else ("", "ed")
        return (
            f"The {prefix}cycle #{self.id} started on {self.start.strftime('%Y-%m-%d')} "
            f"and end{suffix} on {self.end.strftime('%Y-%m-%d')}.\n\n"
            f"**Contributors & Rewards:**\n\n{rewards_info}\n\n"
            f"Cycle total: {self.total_rewards:,}"
        )
