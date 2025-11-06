"""Module with functions for retrieving and saving blockchain data."""

import json
from pathlib import Path

from algosdk import transaction
from algosdk.abi.contract import Contract
from algosdk.account import address_from_private_key
from algosdk.atomic_transaction_composer import (
    AccountTransactionSigner,
    AtomicTransactionComposer,
)
from algosdk.v2client.algod import AlgodClient

from contract.helpers import (
    app_schemas,
    environment_variables,
    private_key_from_mnemonic,
    read_json,
    wait_for_confirmation,
)


def add_allocations(network, addresses, amounts):
    """Add or update allocations for a batch of users.

    :param network: network to deploy to (e.g., "testnet")
    :type network: str
    :param addresses: list of user addresses
    :type addresses: list
    :param amounts: list of corresponding allocation amounts
    :type amounts: list
    :var env: environment variables collection
    :type env: dict
    :var client: Algorand Node client instance
    :type client: :class:`AlgodClient`
    :var token_id: Algorand standard asset identifier to be distributed
    :type token_id: int
    :var atc_stub: collection of data required to create atomic transaction
    :type atc_stub: dict
    :var atc: clear program source code
    :type atc: :class:`AtomicTransactionComposer`
    :var response: atomic transaction creation response
    :type response: :class:`AtomicTransactionResponse`
    """
    env = environment_variables()

    client = AlgodClient(
        env.get(f"algod_token_{network}"), env.get(f"algod_address_{network}")
    )
    token_id = int(env.get(f"rewards_token_id_{network}"))
    atc_stub = atc_method_stub(client, network)
    atc = AtomicTransactionComposer()

    atc.add_method_call(
        app_id=atc_stub.get("app_id"),
        method=atc_stub.get("contract").get_method_by_name("add_allocations"),
        sender=atc_stub.get("sender"),
        sp=atc_stub.get("sp"),
        signer=atc_stub.get("signer"),
        method_args=[addresses, amounts],
        foreign_assets=[token_id],
    )
    response = atc.execute(client, 2)
    print(f"Allocations added in transaction {response.tx_ids[0]}")


def atc_method_stub(client, network):
    """Return instances needed for calling a method with AtomicTransactionComposer.

    :param client: Algorand Node client instance.
    :type client: :class:`AlgodClient`
    :param network: The network to connect to (e.g., "testnet").
    :type network: str
    :var env: Environment variables.
    :type env: dict
    :var creator_private_key: The private key of the application creator.
    :type creator_private_key: str
    :var sender: The address of the transaction sender.
    :type sender: str
    :var signer: The transaction signer.
    :type signer: :class:`algosdk.atomic_transaction_composer.AccountTransactionSigner`
    :var dapp_name: name of the smart contract application
    :type dapp_name: str
    :var contract_json: The ARC-56 smart contract specification.
    :type contract_json: dict
    :var contract: Algorand ABI contract instance
    :type contract: :class:`algosdk.abi.contract.Contract`
    :var sp: suggested transaction params
    :type sp: :class:`transaction.SuggestedParams`
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

    dapp_name = env.get("rewards_dapp_name")
    contract_json = read_json(
        Path(__file__).resolve().parent / "artifacts" / f"{dapp_name}.arc56.json"
    )
    contract = Contract.from_json(json.dumps(contract_json))

    sp = client.suggested_params()
    sp.flat_fee = True
    sp.fee = 2000

    app_id = contract_json["networks"][sp.gh]["appID"]

    return {
        "sender": sender,
        "signer": signer,
        "contract": contract,
        "sp": sp,
        "app_id": app_id,
    }


def create_app(client, private_key, approval_program, clear_program, contract_json):
    """Create a new smart contract application on the Algorand blockchain.

    Builds and submits an ApplicationCreate transaction using compiled approval
    and clear programs. Waits for confirmation and returns the resulting app-id
    and genesis hash.

    :param client: Algorand Node client instance.
    :type client: :class:`AlgodClient`
    :param private_key: Creator's private key used to sign the transaction.
    :type private_key: str
    :param approval_program: Compiled TEAL approval program.
    :type approval_program: bytes
    :param clear_program: Compiled TEAL clear program.
    :type clear_program: bytes
    :param contract_json: ARC-56 smart contract specification.
    :type contract_json: dict
    :return: A tuple containing the newly created application ID and genesis hash.
    :rtype: tuple[int, str]
    """
    # define sender as creator
    sender = address_from_private_key(private_key)

    # declare on_complete as NoOp
    on_complete = transaction.OnComplete.NoOpOC.real

    # get node suggested parameters
    params = client.suggested_params()
    # comment out the next two (2) lines to use suggested fees
    params.flat_fee = True
    params.fee = 1000

    global_schema, local_schema = app_schemas(contract_json)

    # create unsigned transaction
    txn = transaction.ApplicationCreateTxn(
        sender,
        params,
        on_complete,
        approval_program,
        clear_program,
        global_schema,
        local_schema,
    )

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    client.send_transactions([signed_txn])

    # await confirmation
    wait_for_confirmation(client, tx_id)

    # display results
    transaction_response = client.pending_transaction_info(tx_id)
    app_id = transaction_response["application-index"]
    print("Created new app id: ", app_id)

    return app_id, params.gh


def delete_app(client, private_key, app_id):
    """Delete an existing application on the Algorand blockchain.

    Builds and submits an ApplicationDelete transaction, waits for confirmation,
    and prints application id removed from the blockchain.

    :param client: Algorand Node client instance
    :type client: :class:`AlgodClient`
    :param private_key: application's creator private key used to sign transaction
    :type private_key: str
    :param app_id: application identifier
    :type app_id: int
    """
    # declare sender
    sender = address_from_private_key(private_key)

    # get node suggested parameters
    params = client.suggested_params()
    # comment out the next two (2) lines to use suggested fees
    params.flat_fee = True
    params.fee = 1000

    # create unsigned transaction
    txn = transaction.ApplicationDeleteTxn(sender, params, app_id)

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    client.send_transactions([signed_txn])

    # await confirmation
    wait_for_confirmation(client, tx_id)

    # display results
    transaction_response = client.pending_transaction_info(tx_id)
    print("Deleted app-id: ", transaction_response["txn"]["txn"]["apid"])


def reclaim_allocation(network, user_address):
    """Reclaim a user's allocation if it has expired.

    :param network: network to deploy to (e.g., "testnet")
    :type network: str
    :param user_address: The address of the user whose allocation is to be reclaimed
    :type user_address: str
    :var env: environment variables collection
    :type env: dict
    :var client: Algorand Node client instance
    :type client: :class:`AlgodClient`
    :var token_id: Algorand standard asset identifier to be distributed
    :type token_id: int
    :var atc_stub: collection of data required to create atomic transaction
    :type atc_stub: dict
    :var atc: clear program source code
    :type atc: :class:`AtomicTransactionComposer`
    :var response: atomic transaction creation response
    :type response: :class:`AtomicTransactionResponse`
    """
    env = environment_variables()

    client = AlgodClient(
        env.get(f"algod_token_{network}"), env.get(f"algod_address_{network}")
    )
    token_id = int(env.get(f"rewards_token_id_{network}"))
    atc_stub = atc_method_stub(client, network)
    atc = AtomicTransactionComposer()

    atc.add_method_call(
        app_id=atc_stub.get("app_id"),
        method=atc_stub.get("contract").get_method_by_name("reclaim_allocation"),
        sender=atc_stub.get("sender"),
        sp=atc_stub.get("sp"),
        signer=atc_stub.get("signer"),
        method_args=[user_address],
        foreign_assets=[token_id],
    )
    response = atc.execute(client, 2)
    print(f"Allocations reclaimed in transaction {response.tx_ids[0]}")
