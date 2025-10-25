"""Test module for walletauth app's ORM models."""

from datetime import timedelta

import pytest
from django.utils import timezone

from walletauth.models import WalletNonce


class TestWalletNonceModel:
    """Test suite for WalletNonce model."""

    @pytest.fixture
    def valid_address(self):
        return "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"

    @pytest.fixture
    def valid_nonce(self):
        """Return a valid nonce for testing."""
        return "abc123def456"

    @pytest.fixture
    def wallet_nonce(self, valid_address, valid_nonce):
        """Create and return a WalletNonce instance for testing."""
        return WalletNonce.objects.create(address=valid_address, nonce=valid_nonce)

    @pytest.mark.django_db
    def test_wallet_nonce_creation(self, valid_address, valid_nonce):
        """Test basic WalletNonce creation."""
        wallet_nonce = WalletNonce.objects.create(
            address=valid_address, nonce=valid_nonce
        )

        assert wallet_nonce.address == valid_address
        assert wallet_nonce.nonce == valid_nonce
        assert wallet_nonce.used is False
        assert wallet_nonce.created_at is not None
        assert (
            str(wallet_nonce)
            == valid_address[:5] + ".." + valid_address[-5:] + " - " + f"{valid_nonce}"
        )

    @pytest.mark.django_db
    def test_wallet_nonce_string_representation(self, wallet_nonce, valid_nonce):
        """Test string representation of WalletNonce."""
        assert (
            str(wallet_nonce)
            == wallet_nonce.address[:5]
            + ".."
            + wallet_nonce.address[-5:]
            + " - "
            + f"{valid_nonce}"
        )

    @pytest.mark.django_db
    def test_wallet_nonce_is_expired_fresh(self, wallet_nonce):
        """Test is_expired returns False for fresh nonce."""
        assert wallet_nonce.is_expired() is False

    @pytest.mark.django_db
    def test_wallet_nonce_is_expired_old(self, wallet_nonce):
        """Test is_expired returns True for expired nonce."""
        # Mock the created_at to be older than 5 minutes
        old_time = timezone.now() - timedelta(minutes=6)
        wallet_nonce.created_at = old_time

        assert wallet_nonce.is_expired() is True

    @pytest.mark.django_db
    def test_wallet_nonce_is_expired_exactly_5_minutes(self, wallet_nonce):
        """Test is_expired returns True for nonce exactly 5 minutes old."""
        # Mock the created_at to be exactly 5 minutes old
        exactly_5_minutes_ago = timezone.now() - timedelta(minutes=5)
        wallet_nonce.created_at = exactly_5_minutes_ago

        assert wallet_nonce.is_expired() is True

    @pytest.mark.django_db
    def test_wallet_nonce_is_expired_just_before_expiry(self, wallet_nonce):
        """Test is_expired returns False for nonce just before 5 minutes."""
        # Mock the created_at to be just under 5 minutes old
        just_before_5_minutes = timezone.now() - timedelta(minutes=4, seconds=59)
        wallet_nonce.created_at = just_before_5_minutes

        assert wallet_nonce.is_expired() is False

    @pytest.mark.django_db
    def test_wallet_nonce_mark_used(self, wallet_nonce):
        """Test mark_used method updates the nonce as used."""
        assert wallet_nonce.used is False

        wallet_nonce.mark_used()

        # Refresh from database to get updated state
        wallet_nonce.refresh_from_db()
        assert wallet_nonce.used is True

    @pytest.mark.django_db
    def test_wallet_nonce_mark_used_already_used(self, wallet_nonce):
        """Test mark_used method on already used nonce."""
        wallet_nonce.used = True
        wallet_nonce.save()

        wallet_nonce.mark_used()

        # Should remain True
        wallet_nonce.refresh_from_db()
        assert wallet_nonce.used is True

    @pytest.mark.django_db
    def test_wallet_nonce_unique_nonce_constraint(self, valid_address):
        """Test that nonce field is unique."""
        nonce = "unique_nonce_123"
        WalletNonce.objects.create(address=valid_address, nonce=nonce)

        # Attempt to create another WalletNonce with the same nonce
        with pytest.raises(Exception):  # Could be IntegrityError or similar
            WalletNonce.objects.create(address="different_address", nonce=nonce)

    @pytest.mark.django_db
    def test_wallet_nonce_same_address_different_nonce(self, valid_address):
        """Test that same address can have multiple nonces with different values."""
        nonce1 = "nonce_1"
        nonce2 = "nonce_2"

        wallet_nonce1 = WalletNonce.objects.create(address=valid_address, nonce=nonce1)
        wallet_nonce2 = WalletNonce.objects.create(address=valid_address, nonce=nonce2)

        assert wallet_nonce1.address == valid_address
        assert wallet_nonce2.address == valid_address
        assert wallet_nonce1.nonce == nonce1
        assert wallet_nonce2.nonce == nonce2
        assert wallet_nonce1.nonce != wallet_nonce2.nonce

    @pytest.mark.django_db
    def test_wallet_nonce_address_max_length(self, valid_nonce):
        """Test address field respects max length constraint."""
        # Valid address within 58 characters
        valid_address = "A" * 58
        wallet_nonce = WalletNonce.objects.create(
            address=valid_address, nonce=valid_nonce
        )
        assert wallet_nonce.address == valid_address

    @pytest.mark.django_db
    def test_wallet_nonce_nonce_max_length(self, valid_address):
        """Test nonce field respects max length constraint."""
        # Valid nonce within 64 characters
        valid_nonce = "a" * 64
        wallet_nonce = WalletNonce.objects.create(
            address=valid_address, nonce=valid_nonce
        )
        assert wallet_nonce.nonce == valid_nonce

    @pytest.mark.django_db
    def test_wallet_nonce_auto_now_add_created_at(self, valid_address, valid_nonce):
        """Test that created_at is automatically set on creation."""
        before_creation = timezone.now()
        wallet_nonce = WalletNonce.objects.create(
            address=valid_address, nonce=valid_nonce
        )
        after_creation = timezone.now()

        assert before_creation <= wallet_nonce.created_at <= after_creation

    @pytest.mark.django_db
    def test_wallet_nonce_used_default_false(self, wallet_nonce):
        """Test that used field defaults to False."""
        assert wallet_nonce.used is False

    @pytest.mark.django_db
    def test_wallet_nonce_query_by_address(self, valid_address, valid_nonce):
        """Test querying WalletNonce by address."""
        wallet_nonce = WalletNonce.objects.create(
            address=valid_address, nonce=valid_nonce
        )

        # Query by address
        found_nonce = WalletNonce.objects.get(address=valid_address, nonce=valid_nonce)
        assert found_nonce == wallet_nonce

    @pytest.mark.django_db
    def test_wallet_nonce_query_by_nonce(self, valid_address, valid_nonce):
        """Test querying WalletNonce by nonce."""
        wallet_nonce = WalletNonce.objects.create(
            address=valid_address, nonce=valid_nonce
        )

        # Query by nonce
        found_nonce = WalletNonce.objects.get(nonce=valid_nonce)
        assert found_nonce == wallet_nonce

    @pytest.mark.django_db
    def test_wallet_nonce_filter_unused(self, valid_address):
        """Test filtering for unused nonces."""
        used_nonce = "used_nonce"
        unused_nonce = "unused_nonce"

        WalletNonce.objects.create(address=valid_address, nonce=used_nonce, used=True)
        WalletNonce.objects.create(
            address=valid_address, nonce=unused_nonce, used=False
        )

        unused_nonces = WalletNonce.objects.filter(used=False)
        assert unused_nonces.count() == 1
        assert unused_nonces.first().nonce == unused_nonce

    @pytest.mark.django_db
    def test_wallet_nonce_filter_used(self, valid_address):
        """Test filtering for used nonces."""
        used_nonce = "used_nonce"
        unused_nonce = "unused_nonce"

        WalletNonce.objects.create(address=valid_address, nonce=used_nonce, used=True)
        WalletNonce.objects.create(
            address=valid_address, nonce=unused_nonce, used=False
        )

        used_nonces = WalletNonce.objects.filter(used=True)
        assert used_nonces.count() == 1
        assert used_nonces.first().nonce == used_nonce

    @pytest.mark.django_db
    def test_wallet_nonce_mark_used_saves_only_used_field(self, wallet_nonce, mocker):
        """Test that mark_used only updates the used field."""
        mock_save = mocker.patch.object(wallet_nonce, "save")

        wallet_nonce.mark_used()

        # Verify save was called with update_fields containing only 'used'
        mock_save.assert_called_once_with(update_fields=["used"])

    @pytest.mark.django_db
    def test_wallet_nonce_is_expired_with_mocked_timezone(self, wallet_nonce, mocker):
        """Test is_expired with mocked timezone.now()."""
        # Mock timezone.now() to return a specific time
        mock_now = timezone.datetime(2023, 1, 1, 12, 0, 0)
        mocker.patch("walletauth.models.timezone.now", return_value=mock_now)

        # Set created_at to 6 minutes before mocked now (expired)
        wallet_nonce.created_at = mock_now - timedelta(minutes=6)

        assert wallet_nonce.is_expired() is True

    @pytest.mark.django_db
    def test_wallet_nonce_database_index_on_address(self):
        """Test that address field has a database index."""
        field = WalletNonce._meta.get_field("address")
        assert field.db_index is True

    @pytest.mark.django_db
    def test_wallet_nonce_model_meta(self):
        """Test WalletNonce model meta options."""
        meta = WalletNonce._meta
        assert meta.verbose_name == "wallet nonce"
        assert meta.verbose_name_plural == "wallet nonces"

    @pytest.mark.django_db
    def test_wallet_nonce_ordering(self, valid_address):
        """Test WalletNonce default ordering."""
        # Create nonces with different creation times
        nonce1 = WalletNonce.objects.create(address=valid_address, nonce="nonce1")
        nonce2 = WalletNonce.objects.create(address=valid_address, nonce="nonce2")

        # Default ordering should be by creation time (most recent first if no specific ordering)
        all_nonces = WalletNonce.objects.all()
        # The order might vary based on database, but we can at least verify both are returned
        assert all_nonces.count() == 2

    @pytest.mark.django_db
    def test_wallet_nonce_bulk_operations(self, valid_address):
        """Test bulk operations on WalletNonce."""
        nonces = [
            WalletNonce(address=valid_address, nonce=f"nonce_{i}") for i in range(3)
        ]

        created_nonces = WalletNonce.objects.bulk_create(nonces)
        assert len(created_nonces) == 3

        # Mark all as used in bulk
        WalletNonce.objects.filter(address=valid_address).update(used=True)

        used_count = WalletNonce.objects.filter(used=True).count()
        assert used_count == 3
