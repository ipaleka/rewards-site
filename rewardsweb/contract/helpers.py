"""Module with Rewards dApp helpers functions."""

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


# # CONTRACT
def app_schemas():
    """Return instances of state schemas for smart contract's global and local apps.

    :param local_ints: total number of local uint states
    :type local_ints: int
    :var local_bytes: total number of local bytes states
    :type local_bytes: int
    :var global_ints: total number of global uint states
    :type global_ints: int
    :var global_bytes: total number of global bytes states
    :type global_bytes: int
    :return: two-tuple
    """
    local_ints = 0
    local_bytes = 0
    global_ints = 2
    global_bytes = 1
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


def load_contract():
    """Load from disk, instantiate and return Permission dApp smart contract object.

    :var contract_json: full path to Permission dApp smart contract file
    :type contract_json: dict
    :return: :class:`Contract`
    """
    contract_json = read_json(
        Path(__file__).resolve().parent / "artifacts" / "Rewards.arc56.json"
    )
    return Contract.undictify(contract_json)


# # HELPERS
def box_name_from_address(address):
    """Return string representation of base64 encoded public Algorand `address`.

    :param address: governance seat address
    :type address: bytes
    :return: str
    """
    return decode_address(address)


def box_writing_parameters(env, network_suffix=""):
    """Instantiate and return arguments needed for writing boxes to blockchain.

    :param env: environment variables collection
    :type env: dict
    :param network_suffix: network suffix for environment variable keys
    :type network_suffix: str
    :var creator_private_key: application creator's base64 encoded private key
    :type creator_private_key: str
    :var sender: application caller's address
    :type sender: str
    :var signer: application caller's signer instance
    :type signer: :class:`AccountTransactionSigner`
    :var contract: application caller's address
    :type contract: :class:`Contract`
    :return: dict
    """
    creator_private_key = private_key_from_mnemonic(
        env.get(f"creator_mnemonic{network_suffix}")
    )
    sender = address_from_private_key(creator_private_key)
    signer = AccountTransactionSigner(creator_private_key)
    contract = load_contract()

    return {"sender": sender, "signer": signer, "contract": contract}


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


def wait_for_confirmation(client, txid):
    """TODO: docstring and tests"""
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
