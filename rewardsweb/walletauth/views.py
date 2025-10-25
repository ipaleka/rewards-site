from django.http import JsonResponse
from django.views import View
from django.contrib.auth import get_user_model, login
from algosdk.v2client.algod import AlgodClient
from algosdk import encoding
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from core.models import Contributor, Profile
from walletauth.models import WalletNonce
import json
import secrets
import algosdk
import base64
import msgpack

User = get_user_model()

# Initialize Algod client (for fallback if needed)
algod_client = AlgodClient(
    algod_token="",
    algod_address="https://mainnet-api.algonode.cloud",
    headers={"User-Agent": "algosdk"},
)


def verify_signed_transaction(stxn):
    """
    Verify the signature of a signed transaction.
    """
    if stxn.signature is None or len(stxn.signature) == 0:
        return False

    public_key = stxn.transaction.sender
    if stxn.authorizing_address is not None:
        public_key = stxn.authorizing_address

    verify_key = VerifyKey(encoding.decode_address(public_key))

    prefixed_message = b"TX" + base64.b64decode(
        encoding.msgpack_encode(stxn.transaction)
    )

    try:
        verify_key.verify(prefixed_message, base64.b64decode(stxn.signature))
        return True
    except BadSignatureError:
        return False


class WalletNonceView(View):
    """Generate nonce for wallet authentication."""

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            address = data.get("address")
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        if not address or not algosdk.encoding.is_valid_address(address):
            return JsonResponse(
                {"error": f"Invalid or missing address: {address}"}, status=400
            )

        nonce = secrets.token_hex(16)
        WalletNonce.objects.create(address=address, nonce=nonce)
        print(f"[WalletNonceView] Generated nonce: {nonce} for address: {address}")
        return JsonResponse({"nonce": nonce})


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
                f"[WalletVerifyView] Missing data - address: {address}, signed_tx: {signed_transaction_base64 is not None}, nonce: {nonce_str}"
            )
            return JsonResponse({"success": False, "error": "Missing data"}, status=400)

        if not algosdk.encoding.is_valid_address(address):
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
            stxn = algosdk.transaction.SignedTransaction.undictify(txn_dict)
            print(
                f"[WalletVerifyView] Decoded signed transaction, sender: {stxn.transaction.sender}, note: {stxn.transaction.note.decode('utf-8') if stxn.transaction.note else 'No note'}"
            )

            # Verify the signature
            verified = verify_signed_transaction(stxn)
            if not verified:
                print(
                    f"[WalletVerifyView] Signature verification failed for address: {address}"
                )
                return JsonResponse(
                    {"success": False, "error": "Invalid signature"}, status=400
                )

            # Check if the note contains the nonce
            note_str = (
                stxn.transaction.note.decode("utf-8") if stxn.transaction.note else ""
            )
            if (
                not note_str.startswith("SIWA:Login to ASA Stats: ")
                or note_str.split("SIWA:Login to ASA Stats: ")[1] != nonce_str
            ):
                print(
                    f"[WalletVerifyView] Note mismatch - expected nonce: {nonce_str}, got note: {note_str}"
                )
                return JsonResponse(
                    {"success": False, "error": "Invalid nonce in transaction"},
                    status=400,
                )

            print(
                f"[WalletVerifyView] Signature and nonce verified for address: {address}"
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
        return JsonResponse({"success": True})
