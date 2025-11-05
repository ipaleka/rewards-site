"""Module with functions for deploying ASA Stats Rewards smart contract to blockchain."""

from pathlib import Path

from algosdk.v2client.algod import AlgodClient

from contract.helpers import (
    compile_program,
    environment_variables,
    private_key_from_mnemonic,
    read_json,
)
from contract.network import create_app


def deploy_app(network="testnet"):
    """Compile ASA Stats Rewards smart contract and deploy it to blockchain.

    :var env: environment variables collection
    :type env: dict
    :var dapp_name: smart contract application's name
    :type dapp_name: str
    :var client: Algorand Node client instance
    :type client: :class:`AlgodClient`
    :var creator_private_key: application creator's base64 encoded private key
    :type creator_private_key: str
    :var approval_program_source: approval program code
    :type approval_program_source: bytes
    :var clear_program_source: clear program code
    :type clear_program_source: bytes
    :var contract_json: full path to smart contract's JSON file
    :type contract_json: dict
    :var approval_program: compiled approval program
    :type approval_program: str
    :var clear_program: compiled clear program
    :type clear_program: str
    :var app_id: ASA Stats Rewards smart contract identifier
    :type app_id: int
    :return: int
    """
    env = environment_variables()

    dapp_name = env.get("rewards_dapp_name")

    client = AlgodClient(
        env.get(f"algod_token_{network}"), env.get(f"algod_address_{network}")
    )
    creator_private_key = private_key_from_mnemonic(
        env.get(f"creator_mnemonic_{network}")
    )

    approval_program_source = (
        open(
            Path(__file__).resolve().parent / "artifacts" / f"{dapp_name}.approval.teal"
        )
        .read()
        .encode()
    )
    clear_program_source = (
        open(Path(__file__).resolve().parent / "artifacts" / f"{dapp_name}.clear.teal")
        .read()
        .encode()
    )
    contract_json = read_json(
        Path(__file__).resolve().parent / "artifacts" / f"{dapp_name}.arc56.json"
    )

    # compile programs
    approval_program = compile_program(client, approval_program_source)
    clear_program = compile_program(client, clear_program_source)

    # create new application
    app_id = create_app(
        client, creator_private_key, approval_program, clear_program, contract_json
    )
    # print("App ID: ", app_id)
    return app_id
