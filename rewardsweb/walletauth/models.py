from django.db import models
from django.utils import timezone
from datetime import timedelta

class WalletNonce(models.Model):
    address = models.CharField(max_length=58, db_index=True)
    nonce = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    def is_expired(self):
        """Consider expired after 5 minutes."""
        return self.created_at < timezone.now() - timedelta(minutes=5)

    def mark_used(self):
        self.used = True
        self.save(update_fields=["used"])
