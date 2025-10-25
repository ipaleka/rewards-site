"""Module containing walletauth app's ORM models."""

from django.db import models
from django.utils import timezone
from datetime import timedelta


class WalletNonce(models.Model):
    """Model used for creating unique secret for wallet authentication."""

    address = models.CharField(max_length=58, db_index=True)
    nonce = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    def __str__(self):
        """Return instance's string representation.

        :return: str
        """
        return self.address[:5] + ".." + self.address[-5:] + " - " + self.nonce

    def is_expired(self):
        """Consider expired after 5 minutes.

        :return: Boolean
        """
        return self.created_at < timezone.now() - timedelta(minutes=5)

    def mark_used(self):
        """Mark this instance as already used."""
        self.used = True
        self.save(update_fields=["used"])
