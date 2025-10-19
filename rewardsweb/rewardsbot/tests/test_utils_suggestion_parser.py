"""Unit tests for :py:mod:`rewardsbot.utils.suggestion_parser` module.

This module contains tests for the SuggestionParser class and its
contribution type parsing functionality.
"""

from rewardsbot.utils.suggestion_parser import SuggestionParser


class TestUtilsSuggestionParser:
    """Testing class for :py:mod:`rewardsbot.utils.suggestion_parser` components."""

    # # SuggestionParser.parse_reward_type - valid types
    def test_utils_suggestion_parser_parse_reward_type_feature_request(self):
        """Test parse_reward_type returns correct format for Feature Request."""
        result = SuggestionParser.parse_reward_type("F")
        assert result == "[F] Feature Request"

    def test_utils_suggestion_parser_parse_reward_type_bug_report(self):
        """Test parse_reward_type returns correct format for Bug Report."""
        result = SuggestionParser.parse_reward_type("B")
        assert result == "[B] Bug Report"

    def test_utils_suggestion_parser_parse_reward_type_admin_task(self):
        """Test parse_reward_type returns correct format for Admin Task."""
        result = SuggestionParser.parse_reward_type("AT")
        assert result == "[AT] Admin Task"

    def test_utils_suggestion_parser_parse_reward_type_content_task(self):
        """Test parse_reward_type returns correct format for Content Task."""
        result = SuggestionParser.parse_reward_type("CT")
        assert result == "[CT] Content Task"

    def test_utils_suggestion_parser_parse_reward_type_issue_creation(self):
        """Test parse_reward_type returns correct format for Issue Creation."""
        result = SuggestionParser.parse_reward_type("IC")
        assert result == "[IC] Issue Creation"

    def test_utils_suggestion_parser_parse_reward_type_twitter_post(self):
        """Test parse_reward_type returns correct format for Twitter Post."""
        result = SuggestionParser.parse_reward_type("TWR")
        assert result == "[TWR] Twitter Post"

    def test_utils_suggestion_parser_parse_reward_type_development(self):
        """Test parse_reward_type returns correct format for Development."""
        result = SuggestionParser.parse_reward_type("D")
        assert result == "[D] Development"

    def test_utils_suggestion_parser_parse_reward_type_ecosystem_research(self):
        """Test parse_reward_type returns correct format for Ecosystem Research."""
        result = SuggestionParser.parse_reward_type("ER")
        assert result == "[ER] Ecosystem Research"

    # # SuggestionParser.parse_reward_type - case sensitivity
    def test_utils_suggestion_parser_parse_reward_type_lowercase_input(self):
        """Test parse_reward_type handles lowercase input (should be case-sensitive)."""
        # The method is case-sensitive, so lowercase should return unknown type
        result = SuggestionParser.parse_reward_type("f")
        assert result == "[f] Unknown Type"

    def test_utils_suggestion_parser_parse_reward_type_mixed_case_input(self):
        """Test parse_reward_type handles mixed case input."""
        result = SuggestionParser.parse_reward_type("At")
        assert result == "[At] Unknown Type"

    # # SuggestionParser.parse_reward_type - invalid types
    def test_utils_suggestion_parser_parse_reward_type_empty_string(self):
        """Test parse_reward_type handles empty string input."""
        result = SuggestionParser.parse_reward_type("")
        assert result == "[] Unknown Type"

    def test_utils_suggestion_parser_parse_reward_type_none_input(self):
        """Test parse_reward_type handles None input."""
        result = SuggestionParser.parse_reward_type(None)
        assert result == "[None] Unknown Type"

    def test_utils_suggestion_parser_parse_reward_type_unknown_type(self):
        """Test parse_reward_type returns unknown format for invalid type."""
        result = SuggestionParser.parse_reward_type("INVALID")
        assert result == "[INVALID] Unknown Type"

    def test_utils_suggestion_parser_parse_reward_type_special_characters(self):
        """Test parse_reward_type handles special characters in input."""
        result = SuggestionParser.parse_reward_type("F-1")
        assert result == "[F-1] Unknown Type"

    def test_utils_suggestion_parser_parse_reward_type_with_spaces(self):
        """Test parse_reward_type handles input with spaces."""
        result = SuggestionParser.parse_reward_type("F ")
        assert result == "[F ] Unknown Type"

    def test_utils_suggestion_parser_parse_reward_type_numeric_input(self):
        """Test parse_reward_type handles numeric input."""
        result = SuggestionParser.parse_reward_type("123")
        assert result == "[123] Unknown Type"

    # # SuggestionParser.parse_reward_type - edge cases
    def test_utils_suggestion_parser_parse_reward_type_single_character_unknown(self):
        """Test parse_reward_type with single character unknown types."""
        unknown_chars = [
            "X",
            "Y",
            "Z",
            "A",
            "C",
            "E",
            "G",
            "H",
            "I",
            "J",
            "K",
            "L",
            "M",
        ]

        for char in unknown_chars:
            result = SuggestionParser.parse_reward_type(char)
            assert result == f"[{char}] Unknown Type"

    def test_utils_suggestion_parser_parse_reward_type_multiple_character_unknown(self):
        """Test parse_reward_type with multiple character unknown types."""
        unknown_types = ["ABC", "XYZ", "TEST", "REWARD", "CONTRIB"]

        for reward_type in unknown_types:
            result = SuggestionParser.parse_reward_type(reward_type)
            assert result == f"[{reward_type}] Unknown Type"

    def test_utils_suggestion_parser_parse_reward_type_whitespace_only(self):
        """Test parse_reward_type with whitespace-only input."""
        result = SuggestionParser.parse_reward_type("   ")
        assert result == "[   ] Unknown Type"

    def test_utils_suggestion_parser_parse_reward_type_very_long_input(self):
        """Test parse_reward_type with very long input string."""
        long_input = "A" * 100
        result = SuggestionParser.parse_reward_type(long_input)
        assert result == f"[{long_input}] Unknown Type"

    # # SuggestionParser.parse_reward_type - method properties
    def test_utils_suggestion_parser_parse_reward_type_is_static_method(self):
        """Test parse_reward_type can be called without class instance."""
        # Should work without creating an instance
        result = SuggestionParser.parse_reward_type("F")
        assert result == "[F] Feature Request"

    def test_utils_suggestion_parser_parse_reward_type_returns_string(self):
        """Test parse_reward_type always returns string type."""
        test_cases = ["F", "INVALID", "", None, "123", "B"]

        for test_input in test_cases:
            result = SuggestionParser.parse_reward_type(test_input)
            assert isinstance(result, str)

    def test_utils_suggestion_parser_parse_reward_type_consistent_format(self):
        """Test parse_reward_type returns consistent format for all inputs."""
        test_cases = [
            ("F", "[F] Feature Request"),
            ("INVALID", "[INVALID] Unknown Type"),
            ("", "[] Unknown Type"),
            ("AT", "[AT] Admin Task"),
            ("nonexistent", "[nonexistent] Unknown Type"),
        ]

        for input_type, expected_format in test_cases:
            result = SuggestionParser.parse_reward_type(input_type)
            assert result == expected_format

    # # SuggestionParser.parse_reward_type - all known types
    def test_utils_suggestion_parser_parse_reward_type_all_known_types(self):
        """Test parse_reward_type with all known contribution types."""
        known_types = {
            "F": "[F] Feature Request",
            "B": "[B] Bug Report",
            "AT": "[AT] Admin Task",
            "CT": "[CT] Content Task",
            "IC": "[IC] Issue Creation",
            "TWR": "[TWR] Twitter Post",
            "D": "[D] Development",
            "ER": "[ER] Ecosystem Research",
        }

        for reward_type, expected_result in known_types.items():
            result = SuggestionParser.parse_reward_type(reward_type)
            assert result == expected_result, f"Failed for type: {reward_type}"

    # # SuggestionParser.parse_reward_type - integration style tests
    def test_utils_suggestion_parser_parse_reward_type_typical_usage_scenarios(self):
        """Test parse_reward_type with typical usage scenarios."""
        # Scenario 1: User provides uppercase valid type
        result1 = SuggestionParser.parse_reward_type("F")
        assert result1 == "[F] Feature Request"

        # Scenario 2: User provides valid multi-character type
        result2 = SuggestionParser.parse_reward_type("TWR")
        assert result2 == "[TWR] Twitter Post"

        # Scenario 3: User provides invalid type
        result3 = SuggestionParser.parse_reward_type("UNKNOWN")
        assert result3 == "[UNKNOWN] Unknown Type"

        # Scenario 4: User provides empty input
        result4 = SuggestionParser.parse_reward_type("")
        assert result4 == "[] Unknown Type"

    def test_utils_suggestion_parser_parse_reward_type_ordering_consistency(self):
        """Test parse_reward_type maintains consistent behavior across multiple calls."""
        # Multiple calls with same input should return same result
        result1 = SuggestionParser.parse_reward_type("B")
        result2 = SuggestionParser.parse_reward_type("B")
        result3 = SuggestionParser.parse_reward_type("B")

        assert result1 == result2 == result3 == "[B] Bug Report"

        # Different inputs should return different results
        result_f = SuggestionParser.parse_reward_type("F")
        result_b = SuggestionParser.parse_reward_type("B")

        assert result_f != result_b
        assert result_f == "[F] Feature Request"
        assert result_b == "[B] Bug Report"
