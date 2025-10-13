"""Module containing website's admin UI setup."""

from django.contrib import admin

from core.models import (
    Contribution,
    Contributor,
    Cycle,
    Handle,
    Reward,
    RewardType,
    SocialPlatform,
)

admin.site.register(Contributor)
admin.site.register(SocialPlatform)
admin.site.register(Handle)
admin.site.register(Cycle)
admin.site.register(RewardType)
admin.site.register(Reward)
admin.site.register(Contribution)
