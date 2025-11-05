"""Module with Rewards smart contract's helpers functions."""

import base64
import json
import os
import time
from pathlib import Path

from algosdk.abi.contract import Contract
from algosdk.account import address_from_private_key
from algosdk.atomic_transaction_composer import AccountTransactionSigner
from algosdk.encoding import decode_address
from algosdk.mnemonic import to_private_key
from algosdk.transaction import StateSchema
from dotenv import load_dotenv

DAPP_NAME = "Rewards"


# # HELPERS
def box_name_from_address(address):
    """Return string representation of base64 encoded public Algorand `address`.

    :param address: governance seat address
    :type address: bytes
    :return: str
    """
    return decode_address(address)


def environment_variables():
    """Return collection of required environment variables.

    :return: dict
    """
    load_dotenv()
    return {
        "algod_token_testnet": os.getenv("ALGOD_TOKEN_TESTNET"),
        "algod_token_mainnet": os.getenv("ALGOD_TOKEN_MAINNET"),
        "algod_address_testnet": os.getenv("ALGOD_ADDRESS_TESTNET"),
        "algod_address_mainnet": os.getenv("ALGOD_ADDRESS_MAINNET"),
        "creator_mnemonic_testnet": os.getenv("CREATOR_MNEMONIC_TESTNET"),
        "creator_mnemonic_mainnet": os.getenv("CREATOR_MNEMONIC_MAINNET"),
        "user_mnemonic_testnet": os.getenv("USER_MNEMONIC_TESTNET"),
        "user_mnemonic_mainnet": os.getenv("USER_MNEMONIC_MAINNET"),
        "rewards_token_id_testnet": os.getenv("REWARDS_TOKEN_ID_TESTNET"),
        "rewards_token_id_mainnet": os.getenv("REWARDS_TOKEN_ID_MAINNET"),
        "rewards_dapp_name": os.getenv("REWARDS_DAPP_NAME"),
        "claim_period_duration": os.getenv("CLAIM_PERIOD_DURATION"),
    }


def pause(seconds=1):
    """Sleep for provided number of seconds.

    :param seconds: number of seconds to pause
    :type seconds: int
    """
    time.sleep(seconds)


def private_key_from_mnemonic(passphrase):
    """Return base64 encoded private key created from provided mnemonic `passphrase`.

    :param passphrase: collection of English words separated by spaces
    :type passphrase: str
    :return: str
    """
    return to_private_key(passphrase)


def read_json(filename):
    """Return collection of key and values created from provided `filename` JSON file.

    :param filename: full path to JSON file
    :type filename: :class:`pathlib.Path`
    :return: dict
    """
    if os.path.exists(filename):
        with open(filename, "r") as json_file:
            try:
                return json.load(json_file)
            except json.JSONDecodeError:
                pass
    return {}


# # CONTRACT
def app_schemas(contract_json):
    """Return instances of state schemas for smart contract's global and local apps.

    :param contract_json: full path to smart contract's JSON file
    :type contract_json: dict
    :var schema: smart contract's schema
    :type schema: dict
    :var global_schema: smart contract's global schema
    :type global_schema: dict
    :var local_schema: smart contract's local schema
    :type local_schema: dict
    :var local_bytes: total number of local bytes states
    :type local_bytes: int
    :var global_ints: total number of global uint states
    :type global_ints: int
    :var global_bytes: total number of global bytes states
    :type global_bytes: int
    :return: two-tuple
    """
    schema = contract_json.get("state", {}).get("schema", {})
    global_schema = schema.get("global", {})
    local_schema = schema.get("local", {})

    global_ints = global_schema.get("ints", 0)
    global_bytes = global_schema.get("bytes", 0)
    local_ints = local_schema.get("ints", 0)
    local_bytes = local_schema.get("bytes", 0)

    return StateSchema(global_ints, global_bytes), StateSchema(local_ints, local_bytes)


def compile_program(client, source_code):
    """Collect and return collection of addresses and related values.

    :param client: Algorand Node client instance
    :type client: :class:`AlgodClient`
    :var source_code: approval/clear program code
    :type source_code: bytes
    :var compile_response: compilation response from Node instance
    :type compile_response: dict
    :return: str
    """
    compile_response = client.compile(source_code.decode("utf-8"))
    return base64.b64decode(compile_response["result"])


# # NETWORK
def atc_method_stub(network, genesis_hash):
    """Return instances needed for calling a method with AtomicTransactionComposer.

    :param network: The network to connect to (e.g., "testnet").
    :type network: str
    :param genesis_hash: The network to connect to (e.g., "testnet").
    :type genesis_hash: str
    :var env: Environment variables.
    :type env: dict
    :var creator_private_key: The private key of the application creator.
    :type creator_private_key: str
    :var sender: The address of the transaction sender.
    :type sender: str
    :var signer: The transaction signer.
    :type signer: :class:`algosdk.atomic_transaction_composer.AccountTransactionSigner`
    :var contract_json: The ARC-56 smart contract specification.
    :type contract_json: dict
    :var contract: Algorand ABI contract instance
    :type contract: :class:`algosdk.abi.contract.Contract`
    :var app_id: Rewards dApp unique identifier
    :type app_id: int
    :return: A dictionary with sender, signer, and contract.
    :rtype: dict
    """
    env = environment_variables()
    creator_private_key = private_key_from_mnemonic(
        env.get(f"creator_mnemonic_{network}")
    )
    sender = address_from_private_key(creator_private_key)
    signer = AccountTransactionSigner(creator_private_key)
    contract_json = read_json(
        Path(__file__).resolve().parent / "artifacts" / f"{DAPP_NAME}.arc56.json"
    )
    contract = Contract.from_json(json.dumps(contract_json))
    app_id = contract_json["networks"][genesis_hash]["appID"]

    return {"sender": sender, "signer": signer, "contract": contract, "app_id": app_id}


def wait_for_confirmation(client, txid):
    """Wait for a blockchain transaction to be confirmed.

    Polls Algorand node until the transaction referenced by `txid`
    is confirmed in a round. Prints waiting messages until confirmation
    then returns full pending transaction information.

    :param client: Algorand Node client instance
    :type client: :class:`AlgodClient`
    :param txid: blockchain transaction ID
    :type txid: str
    :return: pending transaction info including confirmed round
    :rtype: dict
    """
    last_round = client.status().get("last-round")
    txinfo = client.pending_transaction_info(txid)
    while not (txinfo.get("confirmed-round") and txinfo.get("confirmed-round") > 0):
        print("Waiting for confirmation...")
        last_round += 1
        client.status_after_block(last_round)
        txinfo = client.pending_transaction_info(txid)
    print(
        "Transaction {} confirmed in round {}.".format(
            txid, txinfo.get("confirmed-round")
        )
    )
    return txinfo
