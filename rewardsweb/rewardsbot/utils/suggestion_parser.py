class SuggestionParser:
    @staticmethod
    def parse_reward_type(reward_type):
        reward_types = {
            "F": "[F] Feature Request",
            "B": "[B] Bug Report",
            "AT": "[AT] Admin Task",
            "CT": "[CT] Content Task",
            "IC": "[IC] Issue Creation",
            "TWR": "[TWR] Twitter Post",
            "D": "[D] Development",
            "ER": "[ER] Ecosystem Research",
        }
        return reward_types.get(reward_type, f"[{reward_type}] Unknown Type")
