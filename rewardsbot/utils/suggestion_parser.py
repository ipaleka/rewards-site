class SuggestionParser:
    @staticmethod
    def parse_reward_type(reward_type):
        reward_types = {
            "CT": "[CT] Content Task",
            "TWR": "[TWR] Twitter Post",
            "F": "[F] Feature Request",
            "D": "[D] Development",
            "IC": "[IC] Issue Creation",
            "S": "[S] Suggestion",
            "B": "[B] Bug Report",
            "AT": "[AT] Admin Task",
        }
        return reward_types.get(reward_type, f"[{reward_type}] Unknown Type")
