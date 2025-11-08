"""Module containing views for wallet authorization and authentication."""

import base64
import json
from secrets import token_hex

import msgpack
from algosdk.encoding import is_valid_address
from algosdk.transaction import SignedTransaction
from django.contrib.auth import get_user_model, login
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Contributor, Profile
from utils.constants.core import (
    ALGORAND_WALLETS,
    WALLET_CONNECT_NETWORK_OPTIONS,
    WALLET_CONNECT_NONCE_PREFIX,
)
from utils.helpers import verify_signed_transaction
from walletauth.models import WalletNonce

User = get_user_model()


class WalletsAPIView(APIView):
    """Retrieve a list of supported wallets.

    :param request: HTTP request object
    :return: JSON response containing supported wallets
    """

    def get(self, request, *args, **kwargs):
        """Handle GET request to return supported wallets.

        :param request: HTTP request object
        :return: JSON list of supported wallets, each containing:
            - id (str): wallet identifier
            - name (str): user-friendly wallet name
        """
        wallets = ALGORAND_WALLETS
        return Response(wallets)


class ActiveNetworkAPIView(APIView):
    """Get or update the active network stored in the session.

    - `GET` returns the currently active network (default: `testnet`)
    - `POST` sets a new active network

    :param request: HTTP request object
    :return: JSON response with network information or error
    """

    def get(self, request, *args, **kwargs):
        """Handle GET request to retrieve the active network.

        :param request: HTTP request object
        :return: JSON response with:
            - network (str): current active network name
        """
        active_network = request.session.get("active_network", "testnet")
        return Response({"network": active_network})

    def post(self, request, *args, **kwargs):
        """Handle POST request to set the active network.

        Expects JSON with:
            - network (str): network to set (must be in `WALLET_CONNECT_NETWORK_OPTIONS`)

        :param request: HTTP request object
        :return: JSON response with:
            - success (bool): True if network was updated
            - network (str): network that was set
            OR
            - error (str): message if invalid input provided
        """
        try:
            # DRF Request gives request.data. Django Request gives request.body.
            data = getattr(request, "data", None)
            if data is None:
                data = json.loads(request.body)

            network = data.get("network")

        except Exception:
            return Response({"error": "Invalid JSON"}, status=400)

        if network not in WALLET_CONNECT_NETWORK_OPTIONS:
            return Response({"error": "Invalid network"}, status=400)

        request.session["active_network"] = network
        return Response({"success": True, "network": network})


class AddAllocationsAPIView(APIView):
    """Provide data for adding new allocations."""

    def post(self, request, *args, **kwargs):
        """Return allocation data for the received address.

        Expected JSON:
            - address (str): Algorand wallet address

        :param request: HTTP request object
        :return: JSON response with:
            - addresses (list[str])
            - amounts (list[int])
            OR error message
        """
        try:
            data = getattr(request, "data", None)
            if data is None:
                data = json.loads(request.body.decode())

            address = data.get("address")

        except Exception:
            return Response({"error": "Invalid JSON"}, status=400)

        if not address or not is_valid_address(address):
            return Response(
                {"error": f"Invalid or missing address: {address}"}, status=400
            )

        allocations = {"addresses": [], "amounts": []}
        return Response(allocations)


class ClaimAllocationAPIView(APIView):
    """Check if a user has a claimable allocation."""

    def post(self, request, *args, **kwargs):
        """Return whether allocation exists for given address.

        Expected JSON:
            - address (str)

        :param request: HTTP request object
        :return: JSON response with:
            - claimable (bool)
            OR error message
        """
        try:
            data = getattr(request, "data", None)
            if data is None:
                data = json.loads(request.body.decode())

            address = data.get("address")

        except Exception:
            return Response({"error": "Invalid JSON"}, status=400)

        if not address or not is_valid_address(address):
            return Response(
                {"error": f"Invalid or missing address: {address}"}, status=400
            )

        has_claimable_allocation = False  # TODO: implement box check via SDK
        return Response({"claimable": has_claimable_allocation})


class ReclaimAllocationsAPIView(APIView):
    """Provide a list of allocations that can be reclaimed."""

    def post(self, request, *args, **kwargs):
        """Return reclaimable allocation data.

        Expected JSON:
            - address (str)

        :param request: HTTP request object
        :return: JSON response with reclaimable allocation data
        """
        try:
            data = getattr(request, "data", None)
            if data is None:
                data = json.loads(request.body.decode())

            address = data.get("address")

        except Exception:
            return Response({"error": "Invalid JSON"}, status=400)

        if not address or not is_valid_address(address):
            return Response(
                {"error": f"Invalid or missing address: {address}"}, status=400
            )

        reclaimable_allocations = {"addresses": []}
        return Response(reclaimable_allocations)


class WalletNonceAPIView(APIView):
    """Generate nonce for wallet authentication."""

    def post(self, request, *args, **kwargs):
        """Create nonce linked to address.

        Expected JSON:
            - address (str)

        :param request: HTTP request object
        :return: JSON response with:
            - nonce (str)
            - prefix (str)
        """

        try:
            data = getattr(request, "data", None)
            if data is None:
                data = json.loads(request.body.decode())

            address = data.get("address")

        except Exception:
            return Response({"error": "Invalid JSON"}, status=400)

        if not address or not is_valid_address(address):
            return Response(
                {"error": f"Invalid or missing address: {address}"}, status=400
            )

        nonce = token_hex(16)
        WalletNonce.objects.create(address=address, nonce=nonce)

        return Response({"nonce": nonce, "prefix": WALLET_CONNECT_NONCE_PREFIX})


class WalletVerifyAPIView(APIView):
    """Verify wallet signature and log the user in."""

    def post(self, request, *args, **kwargs):
        """Verify signed transaction and authenticate the user.

        Expected JSON:
            - address (str)
            - signedTransaction (str)
            - nonce (str)

        :return: JSON { "success": bool, "redirect_url": "/" } on success
        """
        try:
            address = request.data.get("address")
            signed_transaction_base64 = request.data.get("signedTransaction")
            nonce_str = request.data.get("nonce")
        except Exception:
            return Response({"success": False, "error": "Invalid request"}, status=400)

        if not address or not signed_transaction_base64 or not nonce_str:
            return Response({"success": False, "error": "Missing data"}, status=400)

        if not is_valid_address(address):
            return Response(
                {"success": False, "error": f"Invalid address: {address}"}, status=400
            )

        try:
            nonce_obj = WalletNonce.objects.get(
                nonce=nonce_str, address=address, used=False
            )
        except WalletNonce.DoesNotExist:
            print(f"[WalletVerifyAPIView] Nonce not found or already used: {nonce_str}")
            return Response(
                {"success": False, "error": "Nonce not found or already used"},
                status=400,
            )

        if nonce_obj.is_expired():
            print(f"[WalletVerifyAPIView] Nonce expired: {nonce_str}")
            return Response({"success": False, "error": "Nonce expired"}, status=400)

        # Decode and verify the signed transaction
        try:
            signed_tx_bytes = base64.b64decode(signed_transaction_base64)
            # Decode msgpack to dict
            txn_dict = msgpack.unpackb(signed_tx_bytes)
            # Undictify to SignedTransaction
            stxn = SignedTransaction.undictify(txn_dict)
            note = (
                stxn.transaction.note.decode("utf-8")
                if stxn.transaction.note
                else "No note"
            )
            print(
                f"[WalletVerifyAPIView] Decoded signed transaction, sender: "
                f"{stxn.transaction.sender}, note: {note}"
            )

            # Verify the signature
            verified = verify_signed_transaction(stxn)
            if not verified:
                print(
                    f"[WalletVerifyAPIView] Signature verification failed "
                    f"for address: {address}"
                )
                return Response(
                    {"success": False, "error": "Invalid signature"}, status=400
                )

            # Check if the note contains the nonce
            note_str = (
                stxn.transaction.note.decode("utf-8") if stxn.transaction.note else ""
            )
            if (
                not note_str.startswith(WALLET_CONNECT_NONCE_PREFIX)
                or note_str.split(WALLET_CONNECT_NONCE_PREFIX)[1] != nonce_str
            ):
                print(
                    f"[WalletVerifyAPIView] Note mismatch - "
                    f"expected nonce: {nonce_str}, got note: {note_str}"
                )
                return Response(
                    {"success": False, "error": "Invalid nonce in transaction"},
                    status=400,
                )

            print(
                f"[WalletVerifyAPIView] Signature and nonce "
                f"verified for address: {address}"
            )

        except Exception as e:
            print(f"[WalletVerifyAPIView] Verification error: {e}")
            return Response(
                {"success": False, "error": "Invalid signed transaction"}, status=400
            )

        nonce_obj.mark_used()
        print(f"[WalletVerifyAPIView] Nonce marked used: {nonce_str}")

        # Link or create user via Contributor
        contributor = Contributor.objects.filter(address=address).first()
        if contributor:
            profile = Profile.objects.filter(contributor=contributor).first()
            if profile:
                user = profile.user
            else:
                user = User.objects.create(username=f"{address[:5]}..{address[-5:]}")
                user.profile.contributor = contributor
                user.profile.save()
        else:
            user = User.objects.create(username=f"{address[:5]}..{address[-5:]}")
            contributor = Contributor.objects.create(
                name=user.username, address=address
            )
            user.profile.contributor = contributor
            user.profile.save()

        print(f"[WalletVerifyAPIView] Logged in user: {user.username}")

        # Set the backend and log in the user
        user.backend = "django.contrib.auth.backends.ModelBackend"
        login(request, user)

        return Response({"success": True, "redirect_url": "/"})
