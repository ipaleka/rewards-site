"""Module containing core app signals."""

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import Profile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create profile instance if user is successfully created.

    Method is called by signal sent from django infrastructure
    after sender instance is saved.

    :param sender: class responsible for signal sending
    :type sender: type
    :param instance: instance of the sender class
    :type instance: :class:`User`
    :param created: value that determines is sender is created or not
    :type created: boolean
    """
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Update profile instance after related user is updated.

    Method is called by signal sent from django infrastructure
    after sender instance is updated.

    :param sender: class responsible for signal sending
    :type sender: :class:`User`
    :param instance: instance of the sender class
    :type instance: object of :class:`User`
    """
    instance.profile.save()
