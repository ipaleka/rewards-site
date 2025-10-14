"""Module containing API serializers."""

from adrf.serializers import ModelSerializer
from core.models import (
    Contribution,
    Contributor,
    Cycle,
    Reward,
    RewardType,
    SocialPlatform,
)


class ContributorSerializer(ModelSerializer):
    class Meta:
        model = Contributor
        fields = ("name", "address")


class CycleSerializer(ModelSerializer):
    class Meta:
        model = Cycle
        fields = ("id", "start", "end")


class SocialPlatformSerializer(ModelSerializer):
    class Meta:
        model = SocialPlatform
        fields = ("name", "prefix")


class RewardTypeSerializer(ModelSerializer):
    class Meta:
        model = RewardType
        fields = ("label", "name")


class RewardSerializer(ModelSerializer):
    class Meta:
        model = Reward
        fields = ("type", "level", "amount", "description")


class ContributionSerializer(ModelSerializer):
    class Meta:
        model = Contribution
        fields = (
            "id",
            "contributor",
            "cycle",
            "platform",
            "reward",
            "percentage",
            "url",
            "comment",
            "confirmed",
        )
