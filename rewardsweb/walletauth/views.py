"""Module containing views for wallet authorization and authentication."""

import base64
import json
from secrets import token_hex

import msgpack
from algosdk.encoding import is_valid_address
from algosdk.transaction import SignedTransaction
from django.http import JsonResponse
from django.views import View
from django.contrib.auth import get_user_model, login

from core.models import Contributor, Profile
from utils.constants.core import WALLET_CONNECT_NONCE_PREFIX
from utils.helpers import verify_signed_transaction
from walletauth.models import WalletNonce

User = get_user_model()


class ClaimAllocationView(View):
    """Check if a user has a claimable allocation."""

    def post(self, request, *args, **kwargs):
        """Return claimable status for the given address.

        :param request: HTTP request object
        :return: JSON response with claimable status
        """
        try:
            data = json.loads(request.body)
            address = data.get("address")
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        if not address or not is_valid_address(address):
            return JsonResponse(
                {"error": f"Invalid or missing address: {address}"}, status=400
            )

        # This is a placeholder for the actual logic to check the Algorand box.
        # You will need to implement this using the Algorand SDK.
        has_claimable_allocation = False  # Replace with actual check

        return JsonResponse({"claimable": has_claimable_allocation})


class AddAllocationsView(View):
    """Provide data for adding new allocations."""

    def post(self, request, *args, **kwargs):
        """Return a list of addresses and amounts for new allocations.

        :param request: HTTP request object
        :return: JSON response with allocation data
        """
        try:
            data = json.loads(request.body)
            address = data.get("address")
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        if not address or not is_valid_address(address):
            return JsonResponse(
                {"error": f"Invalid or missing address: {address}"}, status=400
            )

        # As per your instruction, this is a placeholder.
        # You will replace this with your actual queryset logic.
        allocations = {"addresses": [], "amounts": []}  # Replace with actual data

        return JsonResponse(allocations)


class ReclaimAllocationsView(View):
    """Provide data for reclaiming expired allocations."""

    def post(self, request, *args, **kwargs):
        """Return a list of expired allocations that can be reclaimed.

        :param request: HTTP request object
        :return: JSON response with reclaimable allocation data
        """
        try:
            data = json.loads(request.body)
            address = data.get("address")
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        if not address or not is_valid_address(address):
            return JsonResponse(
                {"error": f"Invalid or missing address: {address}"}, status=400
            )

        # This is a placeholder for the actual logic to check Algorand boxes.
        # You will need to implement this using the Algorand SDK.
        reclaimable_allocations = {"addresses": []}  # Replace with actual data

        return JsonResponse(reclaimable_allocations)


class WalletNonceView(View):
    """Generate nonce for wallet authentication."""

    def post(self, request, *args, **kwargs):
        """Return nonce created for the received address.

        :param request: HTTP request object
        :return: JSON response with success status or error
        """
        try:
            data = json.loads(request.body)
            address = data.get("address")
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        if not address or not is_valid_address(address):
            return JsonResponse(
                {"error": f"Invalid or missing address: {address}"}, status=400
            )

        nonce = token_hex(16)
        WalletNonce.objects.create(address=address, nonce=nonce)
        print(f"[WalletNonceView] Generated nonce: {nonce} for address: {address}")
        return JsonResponse({"nonce": nonce, "prefix": WALLET_CONNECT_NONCE_PREFIX})


class WalletVerifyView(View):
    """Verify wallet signature and log the user in."""

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            address = data.get("address")
            signed_transaction_base64 = data.get("signedTransaction")
            nonce_str = data.get("nonce")

        except (json.JSONDecodeError, KeyError) as e:
            print(f"[WalletVerifyView] Request error: {e}")
            return JsonResponse(
                {"success": False, "error": "Invalid request"}, status=400
            )

        if not address or not signed_transaction_base64 or not nonce_str:
            print(
                f"[WalletVerifyView] Missing data - address: {address}, signed_tx: "
                f"{signed_transaction_base64 is not None}, nonce: {nonce_str}"
            )
            return JsonResponse({"success": False, "error": "Missing data"}, status=400)

        if not is_valid_address(address):
            print(f"[WalletVerifyView] Invalid address: {address}")
            return JsonResponse(
                {"success": False, "error": f"Invalid address: {address}"}, status=400
            )

        try:
            nonce_obj = WalletNonce.objects.get(
                nonce=nonce_str, address=address, used=False
            )
        except WalletNonce.DoesNotExist:
            print(f"[WalletVerifyView] Nonce not found or already used: {nonce_str}")
            return JsonResponse(
                {"success": False, "error": "Nonce not found or already used"},
                status=400,
            )

        if nonce_obj.is_expired():
            print(f"[WalletVerifyView] Nonce expired: {nonce_str}")
            return JsonResponse(
                {"success": False, "error": "Nonce expired"}, status=400
            )

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
                f"[WalletVerifyView] Decoded signed transaction, sender: "
                f"{stxn.transaction.sender}, note: {note}"
            )

            # Verify the signature
            verified = verify_signed_transaction(stxn)
            if not verified:
                print(
                    f"[WalletVerifyView] Signature verification failed "
                    f"for address: {address}"
                )
                return JsonResponse(
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
                    f"[WalletVerifyView] Note mismatch - "
                    f"expected nonce: {nonce_str}, got note: {note_str}"
                )
                return JsonResponse(
                    {"success": False, "error": "Invalid nonce in transaction"},
                    status=400,
                )

            print(
                f"[WalletVerifyView] Signature and nonce "
                f"verified for address: {address}"
            )

        except Exception as e:
            print(f"[WalletVerifyView] Verification error: {e}")
            return JsonResponse(
                {"success": False, "error": "Invalid signed transaction"}, status=400
            )

        nonce_obj.mark_used()
        print(f"[WalletVerifyView] Nonce marked used: {nonce_str}")

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

        print(f"[WalletVerifyView] Logged in user: {user.username}")

        login(request, user)

        return JsonResponse({"success": True, "redirect_url": "/"})
