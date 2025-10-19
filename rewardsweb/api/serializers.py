"""Module containing ASA Stats Rewards API serializers."""

from adrf.serializers import ModelSerializer, Serializer
from rest_framework.serializers import (
    BooleanField,
    CharField,
    DateField,
    DecimalField,
    DictField,
    IntegerField,
    URLField,
)
from core.models import (
    Contribution,
    Contributor,
    Cycle,
    Reward,
    RewardType,
    SocialPlatform,
)


class AggregatedCycleSerializer(Serializer):
    id = IntegerField()
    start = DateField()
    end = DateField()
    contributor_rewards = DictField()
    total_rewards = IntegerField()


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


class HumanizedContributionSerializer(Serializer):
    id = IntegerField()
    contributor_name = CharField()
    cycle_id = IntegerField()
    platform = CharField()
    url = URLField()
    type = CharField()
    level = IntegerField()
    percentage = DecimalField(max_digits=5, decimal_places=2)
    reward = IntegerField()
    confirmed = BooleanField()


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
