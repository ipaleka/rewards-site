"""Testing module for walletauth app's views."""

import json
from unittest import mock

import pytest
from algosdk.transaction import SignedTransaction
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.views import View

from core.models import Contributor, Profile
from utils.constants.core import WALLET_CONNECT_NONCE_PREFIX
from walletauth.models import WalletNonce
from walletauth.views import (
    WalletNonceView,
    WalletVerifyView,
    ClaimAllocationView,
    AddAllocationsView,
    ReclaimAllocationsView,
)

User = get_user_model()


class TestClaimAllocationView:
    """Test suite for ClaimAllocationView."""

    @pytest.fixture
    def view(self):
        return ClaimAllocationView()

    @pytest.fixture
    def rf(self):
        return RequestFactory()

    @pytest.fixture
    def valid_address(self):
        return "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"

    def test_walletauth_claimallocationview_is_subclass_of_view(self):
        assert issubclass(ClaimAllocationView, View)

    @pytest.mark.django_db
    def test_walletauth_claimallocationview_valid_request(
        self, view, rf, valid_address, mocker
    ):
        """Test successful claimable status check for valid address."""
        mocker.patch("walletauth.views.is_valid_address", return_value=True)
        data = {"address": valid_address}
        request = rf.post(
            "/claim-allocation/", data=json.dumps(data), content_type="application/json"
        )

        response = view.post(request)

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert "claimable" in response_data

    def test_walletauth_claimallocationview_invalid_json(self, view, rf):
        """Test handling of invalid JSON."""
        request = rf.post(
            "/claim-allocation/", data="invalid json", content_type="application/json"
        )
        response = view.post(request)
        assert response.status_code == 400
        assert json.loads(response.content) == {"error": "Invalid JSON"}

    def test_walletauth_claimallocationview_missing_address(self, view, rf):
        """Test handling of missing address."""
        request = rf.post(
            "/claim-allocation/", data=json.dumps({}), content_type="application/json"
        )
        response = view.post(request)
        assert response.status_code == 400
        assert "Invalid or missing address" in json.loads(response.content)["error"]


class TestAddAllocationsView:
    """Test suite for AddAllocationsView."""

    @pytest.fixture
    def view(self):
        return AddAllocationsView()

    @pytest.fixture
    def rf(self):
        return RequestFactory()

    @pytest.fixture
    def valid_address(self):
        return "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"

    def test_walletauth_addallocationsview_is_subclass_of_view(self):
        assert issubclass(AddAllocationsView, View)

    @pytest.mark.django_db
    def test_walletauth_addallocationsview_valid_request(
        self, view, rf, valid_address, mocker
    ):
        """Test successful data retrieval for valid address."""
        mocker.patch("walletauth.views.is_valid_address", return_value=True)
        data = {"address": valid_address}
        request = rf.post(
            "/add-allocations/", data=json.dumps(data), content_type="application/json"
        )

        response = view.post(request)

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert "addresses" in response_data
        assert "amounts" in response_data

    def test_walletauth_addallocationsview_invalid_json(self, view, rf):
        """Test handling of invalid JSON."""
        request = rf.post(
            "/add-allocations/", data="invalid json", content_type="application/json"
        )
        response = view.post(request)
        assert response.status_code == 400
        assert json.loads(response.content) == {"error": "Invalid JSON"}

    def test_walletauth_addallocationsview_missing_address(self, view, rf):
        """Test handling of missing address."""
        request = rf.post(
            "/add-allocations/", data=json.dumps({}), content_type="application/json"
        )
        response = view.post(request)
        assert response.status_code == 400
        assert "Invalid or missing address" in json.loads(response.content)["error"]


class TestReclaimAllocationsView:
    """Test suite for ReclaimAllocationsView."""

    @pytest.fixture
    def view(self):
        return ReclaimAllocationsView()

    @pytest.fixture
    def rf(self):
        return RequestFactory()

    @pytest.fixture
    def valid_address(self):
        return "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"

    def test_walletauth_reclaimallocationsview_is_subclass_of_view(self):
        assert issubclass(ReclaimAllocationsView, View)

    @pytest.mark.django_db
    def test_walletauth_reclaimallocationsview_valid_request(
        self, view, rf, valid_address, mocker
    ):
        """Test successful data retrieval for valid address."""
        mocker.patch("walletauth.views.is_valid_address", return_value=True)
        data = {"address": valid_address}
        request = rf.post(
            "/reclaim-allocations/",
            data=json.dumps(data),
            content_type="application/json",
        )

        response = view.post(request)

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert "addresses" in response_data

    def test_walletauth_reclaimallocationsview_invalid_json(self, view, rf):
        """Test handling of invalid JSON."""
        request = rf.post(
            "/reclaim-allocations/",
            data="invalid json",
            content_type="application/json",
        )
        response = view.post(request)
        assert response.status_code == 400
        assert json.loads(response.content) == {"error": "Invalid JSON"}

    def test_walletauth_reclaimallocationsview_missing_address(self, view, rf):
        """Test handling of missing address."""
        request = rf.post(
            "/reclaim-allocations/",
            data=json.dumps({}),
            content_type="application/json",
        )
        response = view.post(request)
        assert response.status_code == 400
        assert "Invalid or missing address" in json.loads(response.content)["error"]


class TestWalletNonceView:
    """Test suite for WalletNonceView."""

    @pytest.fixture
    def view(self):
        return WalletNonceView()

    @pytest.fixture
    def rf(self):
        return RequestFactory()

    @pytest.fixture
    def valid_address(self):
        return "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"

    def test_walletauth_walletnonceview_is_subclass_of_view(self):
        assert issubclass(WalletNonceView, View)

    @pytest.mark.django_db
    def test_walletauth_walletnonceview_valid_request(
        self, view, rf, valid_address, mocker
    ):
        """Test successful nonce generation for valid address."""
        # Mock the is_valid_address to return True for our test address
        mocker.patch("walletauth.views.is_valid_address", return_value=True)

        data = {"address": valid_address}
        request = rf.post(
            "/nonce/", data=json.dumps(data), content_type="application/json"
        )

        response = view.post(request)

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert "nonce" in response_data
        assert response_data["prefix"] == WALLET_CONNECT_NONCE_PREFIX
        assert WalletNonce.objects.filter(
            address=valid_address, nonce=response_data["nonce"]
        ).exists()

    def test_walletauth_walletnonceview_invalid_json(self, view, rf):
        """Test handling of invalid JSON."""
        request = rf.post(
            "/nonce/", data="invalid json", content_type="application/json"
        )

        response = view.post(request)

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert response_data["error"] == "Invalid JSON"

    def test_walletauth_walletnonceview_missing_address(self, view, rf):
        """Test handling of missing address."""
        data = {}
        request = rf.post(
            "/nonce/", data=json.dumps(data), content_type="application/json"
        )

        response = view.post(request)

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert "Invalid or missing address" in response_data["error"]

    def test_walletauth_walletnonceview_invalid_address(self, view, rf, mocker):
        """Test handling of invalid address."""
        mocker.patch("walletauth.views.is_valid_address", return_value=False)

        data = {"address": "invalid_address"}
        request = rf.post(
            "/nonce/", data=json.dumps(data), content_type="application/json"
        )

        response = view.post(request)

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert "Invalid or missing address" in response_data["error"]


class TestWalletVerifyView:
    """Test suite for WalletVerifyView."""

    @pytest.fixture
    def view(self):
        return WalletVerifyView()

    @pytest.fixture
    def rf(self):
        return RequestFactory()

    @pytest.fixture
    def valid_address(self):
        return "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"

    @pytest.fixture
    def valid_nonce(self):
        return "abc123def456"

    @pytest.fixture
    def mock_signed_transaction(self, valid_nonce):
        """Create a mock signed transaction with proper note."""
        mock_stxn = mock.MagicMock(spec=SignedTransaction)
        mock_stxn.signature = "mock_signature"
        mock_stxn.transaction = mock.MagicMock()
        mock_stxn.transaction.sender = "A" + "B" * 57
        # Create a mock note that can be decoded
        mock_note = mock.MagicMock()
        mock_note.decode.return_value = f"{WALLET_CONNECT_NONCE_PREFIX}{valid_nonce}"
        mock_stxn.transaction.note = mock_note
        mock_stxn.authorizing_address = None
        return mock_stxn

    @pytest.fixture
    def mock_wallet_nonce(self, valid_address, valid_nonce):
        """Create a mock WalletNonce object."""
        mock_nonce = mock.MagicMock(spec=WalletNonce)
        mock_nonce.nonce = valid_nonce
        mock_nonce.address = valid_address
        mock_nonce.used = False
        mock_nonce.is_expired.return_value = False
        mock_nonce.mark_used = mock.MagicMock()
        return mock_nonce

    def setup_method(self):
        """Setup method to mock is_valid_address for all tests."""
        # Mock is_valid_address to return True by default
        self.is_valid_address_patcher = mock.patch(
            "walletauth.views.is_valid_address", return_value=True
        )
        self.mock_is_valid_address = self.is_valid_address_patcher.start()

    def teardown_method(self):
        """Teardown method to stop patchers."""
        self.is_valid_address_patcher.stop()

    def test_walletauth_walletverifyview_is_subclass_of_view(self):
        assert issubclass(WalletVerifyView, View)

    def test_walletauth_walletverifyview_invalid_json(self, view, rf):
        """Test handling of invalid JSON."""
        request = rf.post(
            "/verify/", data="invalid json", content_type="application/json"
        )

        response = view.post(request)

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert response_data == {"success": False, "error": "Invalid request"}

    def test_walletauth_walletverifyview_missing_data(self, view, rf, valid_address):
        """Test handling of missing required data."""
        data = {"address": valid_address}  # Missing signedTransaction and nonce
        request = rf.post(
            "/verify/", data=json.dumps(data), content_type="application/json"
        )

        response = view.post(request)

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert response_data == {"success": False, "error": "Missing data"}

    def test_walletauth_walletverifyview_invalid_address(self, view, rf):
        """Test handling of invalid address."""
        # Override the mock for this specific test
        self.mock_is_valid_address.return_value = False

        data = {
            "address": "invalid_address",
            "signedTransaction": "base64_encoded_tx",
            "nonce": "abc123",
        }
        request = rf.post(
            "/verify/", data=json.dumps(data), content_type="application/json"
        )

        response = view.post(request)

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert response_data == {
            "success": False,
            "error": "Invalid address: invalid_address",
        }

    def test_walletauth_walletverifyview_nonce_not_found(
        self, view, rf, valid_address, mocker
    ):
        """Test handling of non-existent nonce."""
        data = {
            "address": valid_address,
            "signedTransaction": "base64_encoded_tx",
            "nonce": "nonexistent_nonce",
        }
        request = rf.post(
            "/verify/", data=json.dumps(data), content_type="application/json"
        )

        mocker.patch(
            "walletauth.views.WalletNonce.objects.get",
            side_effect=WalletNonce.DoesNotExist,
        )

        response = view.post(request)

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert response_data == {
            "success": False,
            "error": "Nonce not found or already used",
        }

    def test_walletauth_walletverifyview_nonce_expired(
        self, view, rf, valid_address, mocker, mock_wallet_nonce
    ):
        """Test handling of expired nonce."""
        data = {
            "address": valid_address,
            "signedTransaction": "base64_encoded_tx",
            "nonce": "expired_nonce",
        }
        request = rf.post(
            "/verify/", data=json.dumps(data), content_type="application/json"
        )

        mock_wallet_nonce.is_expired.return_value = True
        mocker.patch(
            "walletauth.views.WalletNonce.objects.get", return_value=mock_wallet_nonce
        )

        response = view.post(request)

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert response_data == {"success": False, "error": "Nonce expired"}

    def test_walletauth_walletverifyview_invalid_signed_transaction(
        self, view, rf, valid_address, mocker, mock_wallet_nonce
    ):
        """Test handling of invalid signed transaction base64."""
        data = {
            "address": valid_address,
            "signedTransaction": "invalid_base64",
            "nonce": mock_wallet_nonce.nonce,
        }
        request = rf.post(
            "/verify/", data=json.dumps(data), content_type="application/json"
        )

        mocker.patch(
            "walletauth.views.WalletNonce.objects.get", return_value=mock_wallet_nonce
        )
        mocker.patch(
            "walletauth.views.base64.b64decode", side_effect=Exception("Invalid base64")
        )

        response = view.post(request)

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert response_data == {
            "success": False,
            "error": "Invalid signed transaction",
        }

    def test_walletauth_walletverifyview_signature_verification_failed(
        self,
        view,
        rf,
        valid_address,
        mocker,
        mock_wallet_nonce,
        mock_signed_transaction,
    ):
        """Test handling of failed signature verification."""
        data = {
            "address": valid_address,
            "signedTransaction": "base64_encoded_tx",
            "nonce": mock_wallet_nonce.nonce,
        }
        request = rf.post(
            "/verify/", data=json.dumps(data), content_type="application/json"
        )

        mocker.patch(
            "walletauth.views.WalletNonce.objects.get", return_value=mock_wallet_nonce
        )
        mocker.patch("walletauth.views.base64.b64decode", return_value=b"mock_tx_bytes")
        mocker.patch(
            "walletauth.views.msgpack.unpackb", return_value={"mock": "tx_dict"}
        )
        mocker.patch(
            "walletauth.views.SignedTransaction.undictify",
            return_value=mock_signed_transaction,
        )
        mocker.patch("walletauth.views.verify_signed_transaction", return_value=False)

        response = view.post(request)

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert response_data == {"success": False, "error": "Invalid signature"}

    def test_walletauth_walletverifyview_nonce_mismatch_in_note(
        self,
        view,
        rf,
        valid_address,
        mocker,
        mock_wallet_nonce,
        mock_signed_transaction,
    ):
        """Test handling of nonce mismatch in transaction note."""
        data = {
            "address": valid_address,
            "signedTransaction": "base64_encoded_tx",
            "nonce": mock_wallet_nonce.nonce,
        }
        request = rf.post(
            "/verify/", data=json.dumps(data), content_type="application/json"
        )

        # Set up transaction with wrong nonce in note
        mock_signed_transaction.transaction.note.decode.return_value = (
            f"{WALLET_CONNECT_NONCE_PREFIX}wrong_nonce"
        )

        mocker.patch(
            "walletauth.views.WalletNonce.objects.get", return_value=mock_wallet_nonce
        )
        mocker.patch("walletauth.views.base64.b64decode", return_value=b"mock_tx_bytes")
        mocker.patch(
            "walletauth.views.msgpack.unpackb", return_value={"mock": "tx_dict"}
        )
        mocker.patch(
            "walletauth.views.SignedTransaction.undictify",
            return_value=mock_signed_transaction,
        )
        mocker.patch("walletauth.views.verify_signed_transaction", return_value=True)

        response = view.post(request)

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert response_data == {
            "success": False,
            "error": "Invalid nonce in transaction",
        }

    def test_walletauth_walletverifyview_success_new_user(
        self,
        view,
        rf,
        valid_address,
        mocker,
        mock_wallet_nonce,
        mock_signed_transaction,
    ):
        """Test successful verification with new user creation."""
        data = {
            "address": valid_address,
            "signedTransaction": "base64_encoded_tx",
            "nonce": mock_wallet_nonce.nonce,
        }
        request = rf.post(
            "/verify/", data=json.dumps(data), content_type="application/json"
        )

        mocker.patch(
            "walletauth.views.WalletNonce.objects.get", return_value=mock_wallet_nonce
        )
        mocker.patch("walletauth.views.base64.b64decode", return_value=b"mock_tx_bytes")
        mocker.patch(
            "walletauth.views.msgpack.unpackb", return_value={"mock": "tx_dict"}
        )
        mocker.patch(
            "walletauth.views.SignedTransaction.undictify",
            return_value=mock_signed_transaction,
        )
        mocker.patch("walletauth.views.verify_signed_transaction", return_value=True)
        mocker.patch(
            "walletauth.views.Contributor.objects.filter",
            return_value=mock.MagicMock(first=lambda: None),
        )
        mock_user_create = mocker.patch("walletauth.views.User.objects.create")
        mocker.patch("walletauth.views.Contributor.objects.create")
        mock_login = mocker.patch("walletauth.views.login")

        response = view.post(request)

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data == {"success": True, "redirect_url": "/"}
        mock_wallet_nonce.mark_used.assert_called_once()
        mock_user_create.assert_called_once()
        mock_login.assert_called_once()

    def test_walletauth_walletverifyview_success_existing_contributor_no_profile(
        self,
        view,
        rf,
        valid_address,
        mocker,
        mock_wallet_nonce,
        mock_signed_transaction,
    ):
        """Test successful verification with existing contributor but no profile."""
        data = {
            "address": valid_address,
            "signedTransaction": "base64_encoded_tx",
            "nonce": mock_wallet_nonce.nonce,
        }
        request = rf.post(
            "/verify/", data=json.dumps(data), content_type="application/json"
        )

        mock_contributor = mock.MagicMock(spec=Contributor)
        mock_contributor.address = valid_address

        mocker.patch(
            "walletauth.views.WalletNonce.objects.get", return_value=mock_wallet_nonce
        )
        mocker.patch("walletauth.views.base64.b64decode", return_value=b"mock_tx_bytes")
        mocker.patch(
            "walletauth.views.msgpack.unpackb", return_value={"mock": "tx_dict"}
        )
        mocker.patch(
            "walletauth.views.SignedTransaction.undictify",
            return_value=mock_signed_transaction,
        )
        mocker.patch("walletauth.views.verify_signed_transaction", return_value=True)
        mocker.patch(
            "walletauth.views.Contributor.objects.filter",
            return_value=mock.MagicMock(first=lambda: mock_contributor),
        )
        mocker.patch(
            "walletauth.views.Profile.objects.filter",
            return_value=mock.MagicMock(first=lambda: None),
        )
        mock_user_create = mocker.patch("walletauth.views.User.objects.create")
        mock_login = mocker.patch("walletauth.views.login")

        response = view.post(request)

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data == {"success": True, "redirect_url": "/"}
        mock_wallet_nonce.mark_used.assert_called_once()
        mock_user_create.assert_called_once()
        mock_login.assert_called_once()

    def test_walletauth_walletverifyview_success_existing_user(
        self,
        view,
        rf,
        valid_address,
        mocker,
        mock_wallet_nonce,
        mock_signed_transaction,
    ):
        """Test successful verification with existing user."""
        data = {
            "address": valid_address,
            "signedTransaction": "base64_encoded_tx",
            "nonce": mock_wallet_nonce.nonce,
        }
        request = rf.post(
            "/verify/", data=json.dumps(data), content_type="application/json"
        )

        mock_contributor = mock.MagicMock(spec=Contributor)
        mock_contributor.address = valid_address
        mock_profile = mock.MagicMock(spec=Profile)
        mock_user = mock.MagicMock(spec=User)
        mock_profile.user = mock_user

        mocker.patch(
            "walletauth.views.WalletNonce.objects.get", return_value=mock_wallet_nonce
        )
        mocker.patch("walletauth.views.base64.b64decode", return_value=b"mock_tx_bytes")
        mocker.patch(
            "walletauth.views.msgpack.unpackb", return_value={"mock": "tx_dict"}
        )
        mocker.patch(
            "walletauth.views.SignedTransaction.undictify",
            return_value=mock_signed_transaction,
        )
        mocker.patch("walletauth.views.verify_signed_transaction", return_value=True)
        mocker.patch(
            "walletauth.views.Contributor.objects.filter",
            return_value=mock.MagicMock(first=lambda: mock_contributor),
        )
        mocker.patch(
            "walletauth.views.Profile.objects.filter",
            return_value=mock.MagicMock(first=lambda: mock_profile),
        )
        mock_login = mocker.patch("walletauth.views.login")

        response = view.post(request)

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data == {"success": True, "redirect_url": "/"}
        mock_wallet_nonce.mark_used.assert_called_once()
        mock_login.assert_called_once()

    @pytest.mark.django_db
    def test_walletauth_walletverifyview_integration_success(
        self, view, rf, valid_address, mocker, mock_signed_transaction
    ):
        """Integration test for successful wallet verification."""
        # Create a real nonce in database
        nonce_str = "integration_test_nonce"
        wallet_nonce = WalletNonce.objects.create(
            address=valid_address, nonce=nonce_str
        )

        data = {
            "address": valid_address,
            "signedTransaction": "base64_encoded_tx",
            "nonce": nonce_str,
        }
        request = rf.post(
            "/verify/", data=json.dumps(data), content_type="application/json"
        )

        # Set up the mock transaction note to match the integration test nonce
        mock_signed_transaction.transaction.note.decode.return_value = (
            f"{WALLET_CONNECT_NONCE_PREFIX}{nonce_str}"
        )

        mocker.patch("walletauth.views.base64.b64decode", return_value=b"mock_tx_bytes")
        mocker.patch(
            "walletauth.views.msgpack.unpackb", return_value={"mock": "tx_dict"}
        )
        mocker.patch(
            "walletauth.views.SignedTransaction.undictify",
            return_value=mock_signed_transaction,
        )
        mocker.patch("walletauth.views.verify_signed_transaction", return_value=True)
        mocker.patch(
            "walletauth.views.Contributor.objects.filter",
            return_value=mock.MagicMock(first=lambda: None),
        )
        mocker.patch("walletauth.views.User.objects.create")
        mocker.patch("walletauth.views.Contributor.objects.create")
        mocker.patch("walletauth.views.login")

        response = view.post(request)

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data == {"success": True, "redirect_url": "/"}

        # Verify nonce was marked as used
        wallet_nonce.refresh_from_db()
        assert wallet_nonce.used is True

    def test_walletauth_walletverifyview_transaction_note_decoding_error(
        self,
        view,
        rf,
        valid_address,
        mocker,
        mock_wallet_nonce,
        mock_signed_transaction,
    ):
        """Test handling of transaction note decoding errors."""
        data = {
            "address": valid_address,
            "signedTransaction": "base64_encoded_tx",
            "nonce": mock_wallet_nonce.nonce,
        }
        request = rf.post(
            "/verify/", data=json.dumps(data), content_type="application/json"
        )

        # Create a new mock for the note that will raise UnicodeDecodeError
        mock_note_with_error = mock.MagicMock()
        mock_note_with_error.decode.side_effect = UnicodeDecodeError(
            "utf-8", b"", 0, 1, "invalid byte"
        )
        mock_signed_transaction.transaction.note = mock_note_with_error

        mocker.patch(
            "walletauth.views.WalletNonce.objects.get", return_value=mock_wallet_nonce
        )
        mocker.patch("walletauth.views.base64.b64decode", return_value=b"mock_tx_bytes")
        mocker.patch(
            "walletauth.views.msgpack.unpackb", return_value={"mock": "tx_dict"}
        )
        mocker.patch(
            "walletauth.views.SignedTransaction.undictify",
            return_value=mock_signed_transaction,
        )
        mocker.patch("walletauth.views.verify_signed_transaction", return_value=True)

        response = view.post(request)

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert response_data == {
            "success": False,
            "error": "Invalid signed transaction",
        }

    def test_walletauth_walletverifyview_empty_note(
        self,
        view,
        rf,
        valid_address,
        mocker,
        mock_wallet_nonce,
        mock_signed_transaction,
    ):
        """Test handling of empty transaction note."""
        data = {
            "address": valid_address,
            "signedTransaction": "base64_encoded_tx",
            "nonce": mock_wallet_nonce.nonce,
        }
        request = rf.post(
            "/verify/", data=json.dumps(data), content_type="application/json"
        )

        # Set up transaction with empty note
        mock_signed_transaction.transaction.note = None

        mocker.patch(
            "walletauth.views.WalletNonce.objects.get", return_value=mock_wallet_nonce
        )
        mocker.patch("walletauth.views.base64.b64decode", return_value=b"mock_tx_bytes")
        mocker.patch(
            "walletauth.views.msgpack.unpackb", return_value={"mock": "tx_dict"}
        )
        mocker.patch(
            "walletauth.views.SignedTransaction.undictify",
            return_value=mock_signed_transaction,
        )
        mocker.patch("walletauth.views.verify_signed_transaction", return_value=True)

        response = view.post(request)

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert response_data == {
            "success": False,
            "error": "Invalid nonce in transaction",
        }

    def test_walletauth_walletverifyview_note_without_prefix(
        self,
        view,
        rf,
        valid_address,
        mocker,
        mock_wallet_nonce,
        mock_signed_transaction,
    ):
        """Test handling of transaction note without expected prefix."""
        data = {
            "address": valid_address,
            "signedTransaction": "base64_encoded_tx",
            "nonce": mock_wallet_nonce.nonce,
        }
        request = rf.post(
            "/verify/", data=json.dumps(data), content_type="application/json"
        )

        # Set up transaction with note that doesn't start with the prefix
        mock_signed_transaction.transaction.note.decode.return_value = (
            f"WrongPrefix{mock_wallet_nonce.nonce}"
        )

        mocker.patch(
            "walletauth.views.WalletNonce.objects.get", return_value=mock_wallet_nonce
        )
        mocker.patch("walletauth.views.base64.b64decode", return_value=b"mock_tx_bytes")
        mocker.patch(
            "walletauth.views.msgpack.unpackb", return_value={"mock": "tx_dict"}
        )
        mocker.patch(
            "walletauth.views.SignedTransaction.undictify",
            return_value=mock_signed_transaction,
        )
        mocker.patch("walletauth.views.verify_signed_transaction", return_value=True)

        response = view.post(request)

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert response_data == {
            "success": False,
            "error": "Invalid nonce in transaction",
        }

    def test_walletauth_walletverifyview_msgpack_unpack_error(
        self, view, rf, valid_address, mocker, mock_wallet_nonce
    ):
        """Test handling of msgpack unpacking errors."""
        data = {
            "address": valid_address,
            "signedTransaction": "base64_encoded_tx",
            "nonce": mock_wallet_nonce.nonce,
        }
        request = rf.post(
            "/verify/", data=json.dumps(data), content_type="application/json"
        )

        mocker.patch(
            "walletauth.views.WalletNonce.objects.get", return_value=mock_wallet_nonce
        )
        mocker.patch("walletauth.views.base64.b64decode", return_value=b"mock_tx_bytes")
        mocker.patch(
            "walletauth.views.msgpack.unpackb", side_effect=Exception("Msgpack error")
        )

        response = view.post(request)

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert response_data == {
            "success": False,
            "error": "Invalid signed transaction",
        }
