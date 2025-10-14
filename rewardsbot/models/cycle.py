from datetime import datetime


class Cycle:
    def __init__(self, data):

        self.id = data.get("cycleId")
        self.start = datetime.fromisoformat(data.get("start"))
        self.end = datetime.fromisoformat(data.get("end"))
        self.contributors_rewards = data.get("contributorsRewards", {})
        self.total_rewards_cycle = data.get("totalRewardsCycle", 0)

    def get_formatted_cycle_info(self):
        rewards_info = "\n".join(
            f"{name} {reward:.2f} damo"
            for name, reward in self.contributors_rewards.items()
        )

        return (
            f"The current cycle started on {self.start.strftime('%Y-%m-%d')} "
            f"and ends on {self.end.strftime('%Y-%m-%d')}.\n\n"
            f"**Contributors & Rewards:**\n\n{rewards_info}\n\n"
            f"Cycle total: {self.total_rewards_cycle:.2f} damo"
        )
