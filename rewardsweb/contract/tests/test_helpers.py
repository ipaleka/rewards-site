"""Testing module for :py:mod:`contract.helpers` module."""

import base64
import json
from unittest import mock

import pytest

from contract.helpers import (
    app_schemas,
    atc_method_stub,
    box_name_from_address,
    compile_program,
    environment_variables,
    pause,
    private_key_from_mnemonic,
    read_json,
    wait_for_confirmation,
)


# # HELPERS
class TestContractHelpersFunctions:
    """Testing class for :py:mod:`contract.helpers` helpers functions."""

    # # box_name_from_address
    @pytest.mark.parametrize(
        "address,box_name",
        [
            (
                "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU",
                (
                    b"\xd1*l\xf0&t\x97\xb4\xfb\x94\xc0\xc9\xa0\xd0"
                    b"\xd3l\xc3\x9c\xe5h\xef+HA\xb9\xca\xf0!\xb8k\xc6\xf7"
                ),
            ),
            (
                "VW55KZ3NF4GDOWI7IPWLGZDFWNXWKSRD5PETRLDABZVU5XPKRJJRK3CBSU",
                (
                    b"\xad\xbb\xd5gm/\x0c7Y\x1fC\xec\xb3de\xb3oeJ#"
                    b"\xeb\xc98\xac`\x0ekN\xdd\xea\x8aS"
                ),
            ),
            (
                "LXJ3Q6RZ2TJ6VCJDFMSM4ZVNYYYE4KVSL3N2TYR23PLNCJCIXBM3NYTBYE",
                (
                    b"]\xd3\xb8z9\xd4\xd3\xea\x89#+$\xcef\xad\xc60N*"
                    b"\xb2^\xdb\xa9\xe2:\xdb\xd6\xd1$H\xb8Y"
                ),
            ),
            (
                "VKENBO5W2DZAZFQR45SOQO6IMWS5UMVZCHLPEACNOII7BDJTGBZKSEL4Y4",
                (
                    b"\xaa\x88\xd0\xbb\xb6\xd0\xf2\x0c\x96\x11\xe7d"
                    b"\xe8;\xc8e\xa5\xda2\xb9\x11\xd6\xf2\x00Mr\x11\xf0\x8d30r"
                ),
            ),
        ],
    )
    def test_contract_helpers_box_name_from_address_functionality(
        self, address, box_name
    ):
        returned = box_name_from_address(address)
        assert returned == box_name

    # # environment_variables
    def test_contract_helpers_environment_variables_functionality(self, mocker):
        mocks = {}
        for var in (
            "algod_token_testnet",
            "algod_token_mainnet",
            "algod_address_testnet",
            "algod_address_mainnet",
            "creator_mnemonic_testnet",
            "creator_mnemonic_mainnet",
            "user_mnemonic_testnet",
            "user_mnemonic_mainnet",
            "rewards_token_id_testnet",
            "rewards_token_id_mainnet",
            "rewards_dapp_name",
            "claim_period_duration",
            "dapp_minimum_algo",
        ):
            mocks[var] = mocker.MagicMock()
        mocked_load_dotenv = mocker.patch("contract.helpers.load_dotenv")
        with mock.patch(
            "contract.helpers.os.getenv",
            side_effect=list(mocks.values()),
        ) as mocked_getenv:
            returned = environment_variables()
            assert returned == mocks
            calls = [mocker.call(var.upper()) for var in mocks]
            mocked_getenv.assert_has_calls(calls, any_order=True)
            assert mocked_getenv.call_count == len(mocks)
        mocked_load_dotenv.assert_called_once_with()

    # # pause
    def test_contract_helpers_pause_functionality_for_provided_argument(self):
        seconds = 10
        with mock.patch("contract.helpers.time.sleep") as mocked_sleep:
            pause(seconds)
            mocked_sleep.assert_called_once_with(seconds)

    def test_contract_helpers_pause_default_functionality(self):
        with mock.patch("contract.helpers.time.sleep") as mocked_sleep:
            pause()
            mocked_sleep.assert_called_once_with(1)

    # # private_key_from_mnemonic
    def test_contract_helpers_private_key_from_mnemonic_functionality(self, mocker):
        passphrase = mocker.MagicMock()
        mocked_key = mocker.patch("contract.helpers.to_private_key")
        returned = private_key_from_mnemonic(passphrase)
        assert returned == mocked_key.return_value
        mocked_key.assert_called_once_with(passphrase)

    # # read_json
    def test_contract_helpers_read_json_returns_empty_dict_for_no_file(self, mocker):
        path = mocker.MagicMock()
        with (
            mock.patch(
                "contract.helpers.os.path.exists", return_value=False
            ) as mocked_exist,
            mock.patch("contract.helpers.open") as mocked_open,
        ):
            assert read_json(path) == {}
            mocked_exist.assert_called_once_with(path)
            mocked_open.assert_not_called()

    def test_contract_helpers_read_json_returns_empty_dict_for_exception(self, mocker):
        with (
            mock.patch("contract.helpers.os.path.exists", return_value=True),
            mock.patch("contract.helpers.open"),
            mock.patch(
                "contract.helpers.json.load",
                side_effect=json.JSONDecodeError("", "", 0),
            ),
        ):
            assert read_json(mocker.MagicMock()) == {}

    def test_contract_helpers_read_json_returns_json_file_content(self, mocker):
        path = mocker.MagicMock()
        with (
            mock.patch("contract.helpers.os.path.exists", return_value=True),
            mock.patch("contract.helpers.open") as mocked_open,
            mock.patch("contract.helpers.json.load") as mocked_load,
        ):
            assert read_json(path) == mocked_load.return_value
            mocked_open.assert_called_once_with(path, "r")
            mocked_load.assert_called_once_with(
                mocked_open.return_value.__enter__.return_value
            )


# # CONTRACT
class TestContractHelpersContractFunctions:
    """Testing class for :py:mod:`contract.helpers` smart contract functions."""

    # # app_schemas
    def test_contract_helpers_app_schemas_for_no_state(self, mocker):
        schema1, schema2 = mocker.MagicMock(), mocker.MagicMock()
        mocked_schema = mocker.patch(
            "contract.helpers.StateSchema", side_effect=[schema1, schema2]
        )
        contract_json = {}
        returned = app_schemas(contract_json)
        assert returned == (schema1, schema2)
        calls = [mocker.call(0, 0), mocker.call(0, 0)]
        mocked_schema.assert_has_calls(calls, any_order=True)
        assert mocked_schema.call_count == 2

    def test_contract_helpers_app_schemas_for_no_schema(self, mocker):
        schema1, schema2 = mocker.MagicMock(), mocker.MagicMock()
        mocked_schema = mocker.patch(
            "contract.helpers.StateSchema", side_effect=[schema1, schema2]
        )
        contract_json = {"state": {1: 2}}
        returned = app_schemas(contract_json)
        assert returned == (schema1, schema2)
        calls = [mocker.call(0, 0), mocker.call(0, 0)]
        mocked_schema.assert_has_calls(calls, any_order=True)
        assert mocked_schema.call_count == 2

    def test_contract_helpers_app_schemas_for_no_local_schema(self, mocker):
        schema1, schema2 = mocker.MagicMock(), mocker.MagicMock()
        mocked_schema = mocker.patch(
            "contract.helpers.StateSchema", side_effect=[schema1, schema2]
        )
        contract_json = {"state": {"schema": {"global": {"ints": 2, "bytes": 1}}}}
        returned = app_schemas(contract_json)
        assert returned == (schema1, schema2)
        calls = [mocker.call(2, 1), mocker.call(0, 0)]
        mocked_schema.assert_has_calls(calls, any_order=True)
        assert mocked_schema.call_count == 2

    def test_contract_helpers_app_schemas_for_no_global_schema(self, mocker):
        schema1, schema2 = mocker.MagicMock(), mocker.MagicMock()
        mocked_schema = mocker.patch(
            "contract.helpers.StateSchema", side_effect=[schema1, schema2]
        )
        contract_json = {"state": {"schema": {"local": {"ints": 1, "bytes": 2}}}}
        returned = app_schemas(contract_json)
        assert returned == (schema1, schema2)
        calls = [mocker.call(0, 0), mocker.call(1, 2)]
        mocked_schema.assert_has_calls(calls, any_order=True)
        assert mocked_schema.call_count == 2

    def test_contract_helpers_app_schemas_functionality(self, mocker):
        schema1, schema2 = mocker.MagicMock(), mocker.MagicMock()
        mocked_schema = mocker.patch(
            "contract.helpers.StateSchema", side_effect=[schema1, schema2]
        )
        contract_json = {
            "state": {"schema": {"global": {"ints": 1}, "local": {"ints": 1}}}
        }
        returned = app_schemas(contract_json)
        assert returned == (schema1, schema2)
        calls = [mocker.call(1, 0), mocker.call(1, 0)]
        mocked_schema.assert_has_calls(calls, any_order=True)
        assert mocked_schema.call_count == 2

    # # compile_program
    def test_contract_helpers_compile_program_functionality(self, mocker):
        client = mocker.MagicMock()
        source_code = b"source_code"
        result = base64.b64encode(b"result")
        compile_response = {"result": result}
        client.compile.return_value = compile_response
        returned = compile_program(client, source_code)
        assert returned == b"result"


# # NETWORK
class TestContractHelpersNetworkFunctions:
    """Testing class for :py:mod:`contract.helpers`network helper functions."""

    # # atc_method_stub
    def test_contract_helpers_atc_method_stub_functionality(self, mocker):
        network = "testnet"
        genesis_hash = "genesis_hash"

        env = {"creator_mnemonic_testnet": "mnemonic-words-go-here"}
        mocked_env = mocker.patch(
            "contract.helpers.environment_variables", return_value=env
        )

        client = mocker.MagicMock()

        creator_private_key = mocker.MagicMock()
        mocked_private_key = mocker.patch(
            "contract.helpers.private_key_from_mnemonic",
            return_value=creator_private_key,
        )

        sender_address = "SENDER_ADDRESS"
        mocked_address = mocker.patch(
            "contract.helpers.address_from_private_key", return_value=sender_address
        )

        signer_obj = mocker.MagicMock()
        mocked_signer = mocker.patch(
            "contract.helpers.AccountTransactionSigner", return_value=signer_obj
        )

        sp = mocker.MagicMock()
        client.suggested_params.return_value = sp
        genesis_hash = "genesis_hash"
        sp.gh = genesis_hash

        app_id = 5050
        contract_json = {
            "name": "TestContract",
            "networks": {genesis_hash: {"appID": app_id}},
        }
        mocked_read_json = mocker.patch(
            "contract.helpers.read_json", return_value=contract_json
        )

        contract_obj = mocker.MagicMock()
        mocked_contract = mocker.patch(
            "contract.helpers.Contract.from_json", return_value=contract_obj
        )

        returned = atc_method_stub(client, network)

        assert returned == {
            "sender": sender_address,
            "signer": signer_obj,
            "contract": contract_obj,
            "sp": sp,
            "app_id": app_id,
        }

        mocked_env.assert_called_once_with()
        mocked_private_key.assert_called_once_with(env["creator_mnemonic_testnet"])
        mocked_address.assert_called_once_with(creator_private_key)
        mocked_signer.assert_called_once_with(creator_private_key)
        mocked_read_json.assert_called_once()
        mocked_contract.assert_called_once_with(json.dumps(contract_json))

    # # wait_for_confirmation
    def test_contract_helpers_wait_for_confirmation_functionality(self, mocker):
        client = mocker.MagicMock()
        txid = "12345"

        # Simulate pending tx then confirmed tx
        client.status.return_value = {"last-round": 1}
        client.pending_transaction_info.side_effect = [
            {"confirmed-round": None},
            {"confirmed-round": 5},
        ]

        returned = wait_for_confirmation(client, txid)

        assert returned == {"confirmed-round": 5}
        client.status.assert_called_once_with()
        assert client.pending_transaction_info.call_count == 2
        client.status_after_block.assert_called_with(2)
