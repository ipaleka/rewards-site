"""Module with functions for deploying Rewards dApp smart contract to blockchain."""

from pathlib import Path

from algosdk.v2client.algod import AlgodClient

from contract.helpers import (
    compile_program,
    environment_variables,
    private_key_from_mnemonic,
)
from contract.network import create_app


def deploy_app(network="testnet"):
    """Compile Permission dApp smart contract and deploy it to blockchain.

    :var env: environment variables collection
    :type env: dict
    :var client: Algorand Node client instance
    :type client: :class:`AlgodClient`
    :var creator_private_key: application creator's base64 encoded private key
    :type creator_private_key: str
    :var approval_program_source: approval program code
    :type approval_program_source: bytes
    :var clear_program_source: clear program code
    :type clear_program_source: bytes
    :var approval_program: compiled approval program
    :type approval_program: str
    :var clear_program: compiled clear program
    :type clear_program: str
    :var app_id: Permission dApp identifier
    :type app_id: int
    :return: int
    """
    env = environment_variables()

    client = AlgodClient(
        env.get(f"algod_token_{network}"), env.get(f"algod_address_{network}")
    )
    creator_private_key = private_key_from_mnemonic(
        env.get(f"creator_mnemonic_{network}")
    )

    approval_program_source = (
        open(Path(__file__).resolve().parent / "artifacts" / "Rewards.approval.teal")
        .read()
        .encode()
    )
    clear_program_source = (
        open(Path(__file__).resolve().parent / "artifacts" / "Rewards.clear.teal")
        .read()
        .encode()
    )

    # compile programs
    approval_program = compile_program(client, approval_program_source)
    clear_program = compile_program(client, clear_program_source)

    # create new application
    app_id = create_app(client, creator_private_key, approval_program, clear_program)
    # print("App ID: ", app_id)
    return app_id
