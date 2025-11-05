"""Module with functions for deploying ASA Stats Rewards smart contract to blockchain."""

import json
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
    """Compile ASA Stats Rewards smart contract, deploy it, and update the artifact.

    This function orchestrates the deployment process by:
    1. Compiling the TEAL approval and clear programs.
    2. Creating a new application on the specified network.
    3. Capturing the new app ID and the network's genesis hash.
    4. Updating the ARC-56 JSON artifact with the new network information.

    :param network: The network to deploy to (e.g., "testnet").
    :type network: str
    :var env: Environment variables.
    :type env: dict
    :var dapp_name: The name of the smart contract application.
    :type dapp_name: str
    :var client: Algorand Node client.
    :type client: :class:`AlgodClient`
    :var creator_private_key: The private key of the application creator.
    :type creator_private_key: str
    :var approval_program_source: The approval program source code.
    :type approval_program_source: bytes
    :var clear_program_source: The clear program source code.
    :type clear_program_source: bytes
    :var contract_json: The ARC-56 smart contract specification.
    :type contract_json: dict
    :var approval_program: The compiled approval program.
    :type approval_program: str
    :var clear_program: The compiled clear program.
    :type clear_program: str
    :var app_id: The ID of the newly created application.
    :type app_id: int
    :var genesis_hash: The genesis hash of the network.
    :type genesis_hash: str
    :return: The ID of the newly created application.
    :rtype: int
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
    contract_json_path = (
        Path(__file__).resolve().parent / "artifacts" / f"{dapp_name}.arc56.json"
    )
    contract_json = read_json(contract_json_path)

    # compile programs
    approval_program = compile_program(client, approval_program_source)
    clear_program = compile_program(client, clear_program_source)

    # create new application
    app_id, genesis_hash = create_app(
        client, creator_private_key, approval_program, clear_program, contract_json
    )

    # update networks section of smart contract
    if "networks" not in contract_json:
        contract_json["networks"] = {}

    contract_json["networks"][genesis_hash] = {"app_id": app_id}

    # write to file
    with open(contract_json_path, "w") as json_file:
        json.dump(contract_json, json_file, indent=4)

    # print("App ID: ", app_id)
    return app_id
