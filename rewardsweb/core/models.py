"""Module containing website's ORM models."""

from django.db import models
from django.db.models import Sum
from django.db.models.functions import Lower
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.functional import cached_property

from utils.constants.core import ADDRESS_LEN, HANDLE_EXCEPTIONS


def _parse_full_handle(full_handle):
    """Return social platform's prefix and user's handle from provided `full_handle`.

    :param full_handle: contributor's unique identifier (platform prefix and handle)
    :type full_handle: str
    :var prefix: unique social platform's prefix
    :type prefix: str
    :var handle: contributor's handle/username
    :type handle: str
    :var platform: social platform's model instance
    :return: two-tuple
    """
    prefix, handle = "", full_handle
    if "@" in full_handle[:2]:
        prefix = full_handle[: full_handle.index("@") + 1]
        handle = full_handle[full_handle.index("@") + 1 :]

    elif full_handle.startswith("u/"):
        prefix = "u/"
        handle = full_handle[2:]

    return prefix, handle


class ContributorManager(models.Manager):
    """ASA Stats contributor's data manager."""

    def from_full_handle(self, full_handle, address=None):
        """Return contributor model instance created from provided `full_handle`.

        :param full_handle: contributor's unique identifier (platform prefix and handle)
        :type full_handle: str
        :param address: public Algorand address
        :type address: str
        :var prefix: unique social platform's prefix
        :type prefix: str
        :var handle: contributor's handle/username
        :type handle: str
        :var platform: social platform's model instance
        :type platform: :class:`SocialPlatform`
        :var contributor: contributor's model instance
        :type contributor: :class:`Contributor`
        :return: :class:`Handle`
        """
        prefix, handle = _parse_full_handle(full_handle)
        contributor = self.from_handle(handle)
        if contributor:
            return contributor

        platform = get_object_or_404(SocialPlatform, prefix=prefix)
        try:
            handle = get_object_or_404(Handle, platform=platform, handle=handle)

        except Http404:
            contributor = self.model(name=full_handle, address=address)
            contributor.save()
            handle = Handle.objects.create(
                contributor=contributor, platform=platform, handle=handle
            )

        return handle.contributor

    def from_handle(self, handle):
        """Return handle model instance located by provided `handle`.

        :param handle: contributor's handle
        :type handle: str
        :var handles: handle instances collection
        :type handles: :class:`django.db.models.query.QuerySet`
        :var count: total number of located contributors
        :type count: int
        :return: :class:`Contributor`
        """
        handles = Handle.objects.filter(handle=handle)
        if not handles:
            handles = Handle.objects.filter(handle__trigram_similar=handle)

        count = len({handle.contributor_id for handle in handles})
        if count == 1:
            return handles[0].contributor

        elif count == 0 or handle in HANDLE_EXCEPTIONS:
            return None

        raise AssertionError(
            f"Can't locate a single contributor for {handle} {str(handles)}"
        )


class Contributor(models.Model):
    """ASA Stats contributor's data model."""

    name = models.CharField(max_length=50)
    address = models.CharField(max_length=ADDRESS_LEN, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ContributorManager()

    class Meta:
        """Define ordering and fields that make unique indexes."""

        constraints = [
            models.UniqueConstraint(
                "name",
                Lower("name"),
                name="unique_contributor_name",
            ),
            models.UniqueConstraint(
                "address",
                name="unique_contributor_address",
            ),
        ]
        ordering = [Lower("name")]

    def __str__(self):
        """Return contributor's instance string representation.

        :return: str
        """
        return _parse_full_handle(self.name)[1]

    def get_absolute_url(self):
        """Returns the URL to access a detail record for this contributor."""
        return reverse("contributor-detail", args=[str(self.id)])

    @cached_property
    def total_rewards(self):
        """Return sum of all reward amounts for this contributor (cached).

        :return: int
        """
        return self.contribution_set.aggregate(total_rewards=Sum("reward__amount")).get(
            "total_rewards", 0
        )


class SocialPlatform(models.Model):
    """ASA Stats social media platform's data model."""

    name = models.CharField(max_length=50)
    prefix = models.CharField(max_length=2, blank=True)

    class Meta:
        """Define ordering and fields that make unique indexes."""

        constraints = [
            models.UniqueConstraint(
                "name",
                Lower("name"),
                name="unique_socialplatform_name",
            ),
            models.UniqueConstraint(
                "prefix",
                name="unique_socialplatform_prefix",
            ),
        ]
        ordering = [Lower("name")]

    def __str__(self):
        """Return contributor's instance string representation.

        :return: str
        """
        return self.name


class HandleManager(models.Manager):
    """ASA Stats social media handle data manager."""

    def from_address_and_full_handle(self, address, full_handle):
        """Return handle model instance derived from provided `address` and `full_handle`.

        :param address: public Algorand address
        :type address: str
        :param full_handle: contributor's unique identifier (platform prefix and handle)
        :type full_handle: str
        :var prefix: unique social platform's prefix
        :type prefix: str
        :var handle: contributor's handle/username
        :type handle: str
        :var contributor: contributor's model instance
        :type contributor: :class:`Contributor`
        :var platform: social platform's model instance
        :type platform: :class:`SocialPlatform`
        :return: :class:`Handle`
        """
        prefix, handle = _parse_full_handle(full_handle)
        try:
            contributor = get_object_or_404(Contributor, address=address)
        except Http404:
            contributor = Contributor.objects.from_full_handle(
                full_handle, address=address
            )
            contributor.save()

        platform = get_object_or_404(SocialPlatform, prefix=prefix)
        return self.model(contributor=contributor, platform=platform, handle=handle)


class Handle(models.Model):
    """ASA Stats social media handle data model."""

    contributor = models.ForeignKey(Contributor, default=None, on_delete=models.CASCADE)
    platform = models.ForeignKey(SocialPlatform, default=None, on_delete=models.CASCADE)
    handle = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = HandleManager()

    class Meta:
        """Define ordering and fields that make unique indexes."""

        constraints = [
            # Unique handle per platform
            models.UniqueConstraint(
                fields=["platform", "handle"], name="unique_social_handle"
            )
        ]
        ordering = [Lower("handle")]

    def __str__(self):
        """Return contributor's instance string representation.

        :return: str
        """
        return self.handle + "@" + str(self.platform)


class Cycle(models.Model):
    """ASA Stats periodic rewards cycle data model.."""

    start = models.DateField()
    end = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Define model's ordering."""

        ordering = ["start"]

    def __str__(self):
        """Return cycle's instance string representation.

        :return: str
        """
        return (
            self.start.strftime("%d-%m-%y") + " - " + self.end.strftime("%d-%m-%y")
            if self.end
            else ""
        )

    def get_absolute_url(self):
        """Returns the URL to access a detail record for this cycle."""
        return reverse("cycle-detail", args=[str(self.id)])

    @property
    def contributor_rewards(self):
        """Return collection of all contributors and related rewards for cycle (cached).

        TODO: tests

        :return: dict
        """
        result = (
            self.contribution_set.select_related("contributor")
            .values("contributor__name", "confirmed")
            .annotate(total_amount=Sum("reward__amount"))
            .order_by("contributor__name")
        )
        return {
            item["contributor__name"]: (item["total_amount"], item["confirmed"])
            for item in result
        }

    @property
    def total_rewards(self):
        """Return sum of all reward amounts for this cycle (cached).

        :return: int
        """
        return self.contribution_set.aggregate(total_rewards=Sum("reward__amount")).get(
            "total_rewards", 0
        )


class RewardType(models.Model):
    """ASA Stats reward type data model."""

    label = models.CharField(max_length=5, blank=True)
    name = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Define ordering and fields that make unique indexes."""

        constraints = [
            models.UniqueConstraint(
                "label",
                Lower("label"),
                name="unique_rewardtype_label",
            ),
            models.UniqueConstraint(
                "name",
                Lower("name"),
                name="unique_rewardtype_name",
            ),
        ]
        ordering = ["name"]

    def __str__(self):
        """Return reward type's instance string representation.

        :return: str
        """
        return "[" + self.label + "] " + self.name


class Reward(models.Model):
    """ASA Stats reward data model."""

    type = models.ForeignKey(RewardType, default=None, on_delete=models.CASCADE)
    level = models.IntegerField(default=1)
    amount = models.IntegerField(default=10000)
    description = models.CharField(max_length=255, blank=True)
    general_description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Define ordering and fields that make unique indexes."""

        constraints = [
            models.UniqueConstraint(
                fields=["type", "level", "amount"],
                name="unique_reward_type_level_amount",
            ),
        ]
        ordering = ["type", "level"]

    def __str__(self):
        """Return reward's instance string representation.

        :return: str
        """
        return str(self.type) + " " + str(self.level) + ": " + f"{self.amount:,}"


class IssueStatus(models.TextChoices):
    """ASA Stats GitHub channel issue status choices."""

    CREATED = "created", "Created"
    WONTFIX = "wontfix", "Wontfix"
    ADDRESSED = "addressed", "Addressed"
    ARCHIVED = "archived", "Archived"


class Issue(models.Model):
    """ASA Stats GitHub issue model."""

    number = models.IntegerField()
    status = models.CharField(
        max_length=20, choices=IssueStatus.choices, default=IssueStatus.CREATED
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Define ordering and fields that make unique indexes."""

        constraints = [models.UniqueConstraint("number", name="unique_issue_number")]
        ordering = ["-number"]

    def __str__(self):
        """Return reward's instance string representation.

        :return: str
        """
        return str(self.number) + ": " + self.status


class Contribution(models.Model):
    """Community member contributions data model."""

    contributor = models.ForeignKey(Contributor, default=None, on_delete=models.CASCADE)
    cycle = models.ForeignKey(Cycle, default=None, on_delete=models.CASCADE)
    platform = models.ForeignKey(SocialPlatform, default=None, on_delete=models.CASCADE)
    reward = models.ForeignKey(Reward, default=None, on_delete=models.CASCADE)
    issue = models.ForeignKey(Issue, null=True, blank=True, on_delete=models.CASCADE)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    url = models.CharField(max_length=255, null=True)
    comment = models.CharField(max_length=255, null=True)
    confirmed = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Define model's ordering."""

        ordering = ["cycle", "created_at"]

    def __str__(self):
        """Return contribution's instance string representation.

        :return: str
        """
        return (
            self.contributor.name
            + "/"
            + str(self.platform)
            + "/"
            + self.created_at.strftime("%d-%m-%y")
        )

    def get_absolute_url(self):
        """Returns the URL to access a detail record for this contribution."""
        return reverse("contribution-detail", args=[str(self.id)])
