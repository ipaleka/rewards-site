"""ASA Stats Rewards smart contract integration tests module."""

import pytest
from algosdk.account import address_from_private_key
from algosdk.atomic_transaction_composer import AccountTransactionSigner
from algosdk.error import AlgodHTTPError
from algosdk.v2client.algod import AlgodClient

from contract.helpers import (
    box_name_from_address,
    environment_variables,
    private_key_from_mnemonic,
)


# # VALUES
class TestContractIntegrationForNonCreator:
    """Testing class for ASA Stats Rewards smart contract integration tests."""

    # # # delete_box
    # def test_contract_integration_delete_box_raises_error_for_non_creator_caller(self):
    #     env = environment_variables()
    #     client = AlgodClient(
    #         env.get("algod_token_testnet"), env.get("algod_address_testnet")
    #     )
    #     app_id = PERMISSION_APP_ID_TESTNET
    #     address = "KGTSKYBFYC4WHYQ5PLP7FAMGET7OUWPE6AZXJWQAKTMCI4BMZ6FGCPSHPQ"
    #     env["creator_mnemonic_testnet"] = env["user_mnemonic"]
    #     writing_parameters = box_writing_parameters(env, network_suffix="_testnet")
    #     with pytest.raises(AlgodHTTPError) as exception:
    #         delete_box(client, app_id, writing_parameters, address)
    #     assert "logic eval error" in str(exception.value)

    # def test_contract_integration_delete_box_for_creator_caller(self):
    #     env = environment_variables()
    #     client = AlgodClient(
    #         env.get("algod_token_testnet"), env.get("algod_address_testnet")
    #     )
    #     app_id = PERMISSION_APP_ID_TESTNET
    #     address = "KGTSKYBFYC4WHYQ5PLP7FAMGET7OUWPE6AZXJWQAKTMCI4BMZ6FGCPSHPQ"
    #     values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    #     value = serialize_values(values)
    #     writing_parameters = box_writing_parameters(env, network_suffix="_testnet")
    #     write_box(client, app_id, writing_parameters, address, value)
    #     box_name = box_name_from_address(address)
    #     returned = deserialized_permission_dapp_box_value(client, app_id, box_name)
    #     assert returned == values
    #     delete_box(client, app_id, writing_parameters, address)
    #     returned = deserialized_permission_dapp_box_value(client, app_id, box_name)
    #     assert returned is None

    # # # write_box
    # def test_contract_integration_write_box_raises_error_for_non_creator_caller(self):
    #     env = environment_variables()
    #     client = AlgodClient(
    #         env.get("algod_token_testnet"), env.get("algod_address_testnet")
    #     )
    #     app_id = PERMISSION_APP_ID_TESTNET
    #     user_private_key = private_key_from_mnemonic(env.get("user_mnemonic"))
    #     sender = address_from_private_key(user_private_key)
    #     signer = AccountTransactionSigner(user_private_key)
    #     contract = load_contract()
    #     writing_parameters = {"sender": sender, "signer": signer, "contract": contract}
    #     address = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"
    #     value = serialize_values([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
    #     with pytest.raises(AlgodHTTPError) as exception:
    #         write_box(client, app_id, writing_parameters, address, value)
    #     assert "logic eval error" in str(exception.value)

    # def test_contract_integration_write_box_for_creator_caller(self):
    #     env = environment_variables()
    #     client = AlgodClient(
    #         env.get("algod_token_testnet"), env.get("algod_address_testnet")
    #     )
    #     app_id = PERMISSION_APP_ID_TESTNET
    #     writing_parameters = box_writing_parameters(env, network_suffix="_testnet")
    #     address = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"
    #     box_name = box_name_from_address(address)
    #     returned = deserialized_permission_dapp_box_value(client, app_id, box_name)
    #     if returned:
    #         delete_box(client, app_id, writing_parameters, address)
    #     returned = deserialized_permission_dapp_box_value(client, app_id, box_name)
    #     assert returned is None
    #     values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    #     value = serialize_values(values)
    #     write_box(client, app_id, writing_parameters, address, value)
    #     returned = deserialized_permission_dapp_box_value(client, app_id, box_name)
    #     assert returned == values
    #     delete_box(client, app_id, writing_parameters, address)
