"""Testing module for :py:mod:`contract.deploy` module."""

from pathlib import Path
from unittest import mock

import contract.deploy
from contract.deploy import deploy_app, setup_app


class TestContractDeployFunctions:
    """Testing class for :py:mod:`deploy` functions."""

    # # deploy_app
    def test_contract_deploy_deploy_app_for_provided_network(self, mocker):
        algod_token, algod_address, creator_mnemonic = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        dapp_name = "Rewards"
        env = {
            "algod_token_mainnet": algod_token,
            "algod_address_mainnet": algod_address,
            "creator_mnemonic_mainnet": creator_mnemonic,
            "algod_token_testnet": mocker.MagicMock(),
            "algod_address_testnet": mocker.MagicMock(),
            "creator_mnemonic_testnet": mocker.MagicMock(),
            "rewards_dapp_name": dapp_name,
        }
        mocked_env = mocker.patch(
            "contract.deploy.environment_variables", return_value=env
        )
        client = mocker.MagicMock()
        mocked_client = mocker.patch("contract.deploy.AlgodClient", return_value=client)
        creator_private_key = mocker.MagicMock()
        mocked_private_key = mocker.patch(
            "contract.deploy.private_key_from_mnemonic",
            return_value=creator_private_key,
        )
        contract_json = {"contract": "json"}
        mocked_json = mocker.patch(
            "contract.deploy.read_json", return_value=contract_json
        )
        approval_program, clear_program = mocker.MagicMock(), mocker.MagicMock()
        mocked_compile = mocker.patch(
            "contract.deploy.compile_program",
            side_effect=[approval_program, clear_program],
        )
        app_id = 5050
        genesis_hash = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        mocked_create = mocker.patch(
            "contract.deploy.create_app", return_value=(app_id, genesis_hash)
        )
        approval_source, clear_source, json_file = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        contract_json_path = (
            Path(contract.deploy.__file__).resolve().parent
            / "artifacts"
            / f"{dapp_name}.arc56.json"
        )
        with mock.patch(
            "contract.deploy.open",
            side_effect=[approval_source, clear_source, json_file],
        ) as mocked_open, mock.patch("contract.deploy.json.dump") as mocked_dump:
            returned = deploy_app(network="mainnet")
            assert returned == app_id
            calls = [
                mocker.call(
                    Path(contract.deploy.__file__).resolve().parent
                    / "artifacts"
                    / f"{dapp_name}.approval.teal"
                ),
                mocker.call(
                    Path(contract.deploy.__file__).resolve().parent
                    / "artifacts"
                    / f"{dapp_name}.clear.teal"
                ),
                mocker.call(contract_json_path, "w"),
            ]
            mocked_open.assert_has_calls(calls, any_order=True)
            assert mocked_open.call_count == 3
            mocked_dump.assert_called_once_with(
                contract_json, json_file.__enter__.return_value, indent=4
            )
            approval_source.read.assert_called_once_with()
            approval_source.read.return_value.encode.assert_called_once_with()
            clear_source.read.assert_called_once_with()
            clear_source.read.return_value.encode.assert_called_once_with()
        mocked_env.assert_called_once_with()
        mocked_client.assert_called_once_with(algod_token, algod_address)
        mocked_private_key.assert_called_once_with(creator_mnemonic)
        mocked_json.assert_called_once_with(contract_json_path)
        calls = [
            mocker.call(client, approval_source.read.return_value.encode.return_value),
            mocker.call(client, clear_source.read.return_value.encode.return_value),
        ]
        mocked_compile.assert_has_calls(calls, any_order=True)
        assert mocked_compile.call_count == 2
        mocked_create.assert_called_once_with(
            client, creator_private_key, approval_program, clear_program, contract_json
        )

    def test_contract_deploy_deploy_app_functionality(self, mocker):
        algod_token, algod_address, creator_mnemonic = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        dapp_name = "Rewards"
        env = {
            "algod_token_mainnet": mocker.MagicMock(),
            "algod_address_mainnet": mocker.MagicMock(),
            "creator_mnemonic_mainnet": mocker.MagicMock(),
            "algod_token_testnet": algod_token,
            "algod_address_testnet": algod_address,
            "creator_mnemonic_testnet": creator_mnemonic,
            "rewards_dapp_name": dapp_name,
        }
        mocked_env = mocker.patch(
            "contract.deploy.environment_variables", return_value=env
        )
        client = mocker.MagicMock()
        mocked_client = mocker.patch("contract.deploy.AlgodClient", return_value=client)
        creator_private_key = mocker.MagicMock()
        mocked_private_key = mocker.patch(
            "contract.deploy.private_key_from_mnemonic",
            return_value=creator_private_key,
        )
        contract_json = {"contract": "json", "networks": {"foo": "bar"}}
        mocked_json = mocker.patch(
            "contract.deploy.read_json", return_value=contract_json
        )
        approval_program, clear_program = mocker.MagicMock(), mocker.MagicMock()
        mocked_compile = mocker.patch(
            "contract.deploy.compile_program",
            side_effect=[approval_program, clear_program],
        )
        app_id = 5050
        genesis_hash = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        mocked_create = mocker.patch(
            "contract.deploy.create_app", return_value=(app_id, genesis_hash)
        )
        approval_source, clear_source, json_file = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        contract_json_path = (
            Path(contract.deploy.__file__).resolve().parent
            / "artifacts"
            / f"{dapp_name}.arc56.json"
        )
        with mock.patch(
            "contract.deploy.open",
            side_effect=[approval_source, clear_source, json_file],
        ) as mocked_open, mock.patch("contract.deploy.json.dump") as mocked_dump:
            returned = deploy_app()
            assert returned == app_id
            assert (
                "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
                in contract_json["networks"]
            )
            assert contract_json["networks"][
                "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
            ] == {"appID": 5050}
            calls = [
                mocker.call(
                    Path(contract.deploy.__file__).resolve().parent
                    / "artifacts"
                    / f"{dapp_name}.approval.teal"
                ),
                mocker.call(
                    Path(contract.deploy.__file__).resolve().parent
                    / "artifacts"
                    / f"{dapp_name}.clear.teal"
                ),
                mocker.call(contract_json_path, "w"),
            ]
            mocked_open.assert_has_calls(calls, any_order=True)
            assert mocked_open.call_count == 3
            mocked_dump.assert_called_once_with(
                contract_json, json_file.__enter__.return_value, indent=4
            )
            approval_source.read.assert_called_once_with()
            approval_source.read.return_value.encode.assert_called_once_with()
            clear_source.read.assert_called_once_with()
            clear_source.read.return_value.encode.assert_called_once_with()
        mocked_env.assert_called_once_with()
        mocked_client.assert_called_once_with(algod_token, algod_address)
        mocked_private_key.assert_called_once_with(creator_mnemonic)
        mocked_json.assert_called_once_with(contract_json_path)
        calls = [
            mocker.call(client, approval_source.read.return_value.encode.return_value),
            mocker.call(client, clear_source.read.return_value.encode.return_value),
        ]
        mocked_compile.assert_has_calls(calls, any_order=True)
        assert mocked_compile.call_count == 2
        mocked_create.assert_called_once_with(
            client, creator_private_key, approval_program, clear_program, contract_json
        )

    def test_contract_deploy_setup_app_uses_default_network(self, mocker):
        env = {
            "algod_token_testnet": "token_test",
            "algod_address_testnet": "address_test",
            "rewards_token_id_testnet": 1234,
        }

        mocked_env = mocker.patch(
            "contract.deploy.environment_variables", return_value=env
        )

        client = mocker.MagicMock()
        mocked_client = mocker.patch("contract.deploy.AlgodClient", return_value=client)

        app_client = mocker.MagicMock()
        mocked_appclient_instance = mocker.patch(
            "contract.deploy.app_client_instance", return_value=app_client
        )

        mocker.patch("builtins.print")  # silence output during testing

        returned = setup_app()

        mocked_env.assert_called_once_with()
        mocked_client.assert_called_once_with("token_test", "address_test")
        mocked_appclient_instance.assert_called_once_with(client, "testnet")

        app_client.call.assert_called_once_with(
            "setup",
            token_id=1234,
            claim_period_duration=1234,
        )

        assert returned == (1234, 1234)  # ✅ NEW ASSERTION FOR RETURN VALUE

    def test_contract_deploy_setup_app_for_provided_network(self, mocker):
        env = {
            "algod_token_mainnet": "mainnet_token",
            "algod_address_mainnet": "mainnet_address",
            "rewards_token_id_mainnet": 9999,
        }

        mocked_env = mocker.patch(
            "contract.deploy.environment_variables", return_value=env
        )

        client = mocker.MagicMock()
        mocked_client = mocker.patch("contract.deploy.AlgodClient", return_value=client)

        app_client = mocker.MagicMock()
        mocked_appclient_instance = mocker.patch(
            "contract.deploy.app_client_instance", return_value=app_client
        )

        mocker.patch("builtins.print")  # suppress console output

        returned = setup_app(network="mainnet")

        mocked_env.assert_called_once_with()
        mocked_client.assert_called_once_with("mainnet_token", "mainnet_address")
        mocked_appclient_instance.assert_called_once_with(client, "mainnet")

        app_client.call.assert_called_once_with(
            "setup",
            token_id=9999,
            claim_period_duration=9999,
        )

        assert returned == (9999, 9999)  # ✅ NEW ASSERTION FOR RETURN VALUE
