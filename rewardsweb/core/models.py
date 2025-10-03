"""Module containing website's ORM models."""

from django.db import models
from django.db.models.functions import Lower

from utils.constants.core import ADDRESS_LEN


class Contributor(models.Model):
    """ASA Stats contributor's data model."""

    name = models.CharField(max_length=50)
    address = models.CharField(max_length=ADDRESS_LEN, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
        return self.name


class SocialProvider(models.Model):
    """ASA Stats social media provider's data model."""

    name = models.CharField(max_length=50)
    prefix = models.CharField(max_length=2, blank=True)

    class Meta:
        """Define ordering and fields that make unique indexes."""

        constraints = [
            models.UniqueConstraint(
                "name",
                Lower("name"),
                name="unique_socialprovider_name",
            ),
            models.UniqueConstraint(
                "prefix",
                name="unique_socialprovider_prefix",
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

class HandleManager(models.Manager):
    """ASA Stats social media handle data manager."""

    def from_address_and_full_handle(self, address, full_handle):
        """TODO: docstring and tests"""
        prefix, handle = "", full_handle
        if "@" in full_handle[:2]:
            prefix = full_handle[: full_handle.index("@") + 1]
            handle = full_handle[full_handle.index("@") + 1 :]

        elif full_handle.startswith("u/"):
            prefix = "u/"
            handle = full_handle[2:]

        contributor = Contributor.objects.get(address=address)
        provider = SocialProvider.objects.get(prefix=prefix)
        return self.model(contributor=contributor, provider=provider, handle=handle)


class Handle(models.Model):
    """ASA Stats social media handle data model."""

    contributor = models.ForeignKey(Contributor, default=None, on_delete=models.CASCADE)
    provider = models.ForeignKey(SocialProvider, default=None, on_delete=models.CASCADE)
    handle = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = HandleManager()

    class Meta:
        """Define ordering and fields that make unique indexes."""

        constraints = [
            # Unique handle per provider
            models.UniqueConstraint(
                fields=["provider", "handle"], name="unique_social_handle"
            )
        ]
        ordering = [Lower("handle")]

    def __str__(self):
        """Return contributor's instance string representation.

        :return: str
        """
        return self.handle + "@" + str(self.provider)


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


class Contribution(models.Model):
    """Community member contributions data model."""

    contributor = models.ForeignKey(Contributor, default=None, on_delete=models.CASCADE)
    cycle = models.ForeignKey(Cycle, default=None, on_delete=models.CASCADE)
    platform = models.CharField(max_length=20, blank=True)
    url = models.CharField(max_length=255, blank=True)
    type = models.CharField(max_length=20, blank=True)
    level = models.IntegerField(null=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    reward = models.DecimalField(max_digits=10, decimal_places=3, null=True)
    comment = models.CharField(max_length=255, blank=True)
    confirmed = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Define model's ordering."""

        ordering = ["cycle", "created_at"]

    def __str__(self):
        """Return cycle's instance string representation.

        :return: str
        """
        return (
            self.contributor.name
            + "/"
            + self.platform
            + "/"
            + self.created_at.strftime("%d-%m-%y")
        )


class LegacyContribution(models.Model):
    """Previous rewards system data model."""

    contributor = models.ForeignKey(Contributor, default=None, on_delete=models.CASCADE)
    cycle = models.ForeignKey(Cycle, default=None, on_delete=models.CASCADE)
    platform = models.CharField(max_length=20, blank=True)
    url = models.CharField(max_length=255, blank=True)
    type = models.CharField(max_length=20, blank=True)
    level = models.IntegerField(null=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    reward = models.DecimalField(max_digits=10, decimal_places=3, null=True)
    comment = models.CharField(max_length=255, blank=True)
    confirmed = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Define model's ordering."""

        ordering = ["cycle"]

    def __str__(self):
        """Return cycle's instance string representation.

        :return: str
        """
        return (
            self.contributor.name
            + "/"
            + self.platform
            + "/"
            + self.created_at.strftime("%d-%m-%y")
        )


class Reward(models.Model):
    """ASA Stats rewards data model."""

    type = models.CharField(max_length=20, blank=True)
    level = models.IntegerField(default=1)
    reward = models.DecimalField(max_digits=10, decimal_places=3, default=100)
    description = models.CharField(max_length=255, blank=True)
    general_description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Define ordering and fields that make unique indexes."""

        constraints = [
            models.UniqueConstraint(
                fields=["type", "level"], name="unique_reward_type_level"
            ),
        ]
        ordering = ["type", "level"]

    def __str__(self):
        """Return cycle's instance string representation.

        :return: str
        """
        return self.type + " " + str(self.level)
