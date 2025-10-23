from django.http import JsonResponse
from django.views import View
from django.contrib.auth import get_user_model, login
from algosdk.util import verify_bytes
from algosdk.v2client.algod import AlgodClient
from core.models import Profile
from walletauth.models import WalletNonce
import json
import secrets
import algosdk
import base64

User = get_user_model()

# Initialize Algod client (for fallback if needed)
algod_client = AlgodClient(
    algod_token="",
    algod_address="https://mainnet-api.algonode.cloud",
    headers={"User-Agent": "algosdk"},
)


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
            signature = bytes(data.get("signature", []))
            nonce_str = data.get("nonce")
            note = bytes(data.get("note", []))
        except (json.JSONDecodeError, KeyError) as e:
            print(f"[WalletVerifyView] Request error: {e}")
            return JsonResponse(
                {"success": False, "error": "Invalid request"}, status=400
            )

        if not address or not nonce_str or not note:
            print(
                f"[WalletVerifyView] Missing data - address: {address}, nonce: {nonce_str}, note length: {len(note)}"
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

        # Reconstruct the transaction to verify the signature
        try:
            public_key = algosdk.encoding.decode_address(address)
            # Decode genesis_hash with padding fix
            genesis_hash = data.get("suggestedParams", {}).get("genesisHash", "")
            if genesis_hash:
                try:
                    # Add padding if needed
                    genesis_hash = (
                        genesis_hash + "=" * (4 - len(genesis_hash) % 4)
                        if len(genesis_hash) % 4
                        else genesis_hash
                    )
                    genesis_hash = base64.b64decode(genesis_hash)
                except Exception as e:
                    print(
                        f"[WalletVerifyView] Error decoding genesis_hash: {e}, genesis_hash: {genesis_hash}"
                    )
                    return JsonResponse(
                        {"success": False, "error": f"Invalid genesis_hash: {e}"},
                        status=400,
                    )

            # Use client-provided suggested params
            suggested_params = algosdk.transaction.SuggestedParams(
                fee=int(data.get("suggestedParams", {}).get("fee", 1000)),
                first=data.get("suggestedParams", {}).get("firstValid", 0),
                last=data.get("suggestedParams", {}).get("lastValid", 0),
                gh=genesis_hash,
                gen=data.get("suggestedParams", {}).get("genesisID", ""),
                flat_fee=True,
            )
            transaction = algosdk.transaction.PaymentTxn(
                sender=address, receiver=address, amt=0, note=note, sp=suggested_params
            )
            print(f"[WalletVerifyView] Transaction type: {type(transaction)}")
            # Encode transaction to bytes
            encoded_tx = algosdk.encoding.msgpack_encode(transaction.dictify())
            print(
                f"[WalletVerifyView] Encoded transaction type: {type(encoded_tx)}, length: {len(encoded_tx)}"
            )
            # Prefix with "TX" for Algorand transaction signing
            message_to_verify = b"TX" + encoded_tx
            print(
                f"[WalletVerifyView] Verifying transaction with note: {note.decode('utf-8')}, signature length: {len(signature)}, encoded_tx length: {len(encoded_tx)}"
            )
            verified = verify_bytes(message_to_verify, signature, public_key)
        except Exception as e:
            print(f"[WalletVerifyView] Verification error: {e}")
            verified = False

        if not verified:
            print(f"[WalletVerifyView] Invalid signature for address: {address}")
            return JsonResponse(
                {"success": False, "error": "Invalid signature"}, status=400
            )

        nonce_obj.mark_used()
        print(f"[WalletVerifyView] Nonce marked used: {nonce_str}")

        profile = Profile.objects.filter(address=address).first()
        if profile:
            user = profile.user
        else:
            user = User.objects.create(username=address[:12])
            profile = Profile.objects.create(user=user, address=address)
        print(f"[WalletVerifyView] Logged in user: {user.username}")

        login(request, user)
        return JsonResponse({"success": True})
