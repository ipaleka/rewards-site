"""Testing module for :py:mod:`contract.network` module."""

import json

from contract.network import (
    add_allocations,
    atc_method_stub,
    create_app,
    delete_app,
    fund_app,
    reclaim_allocation,
)


class TestContractNetworkFunctions:
    """Testing class for :py:mod:`contract.network` functions."""

    # # add_allocations
    def test_contract_network_add_allocations_functionality(self, mocker):
        network = "testnet"
        addresses = ["ADDR1", "ADDR2"]
        amounts = [100, 200]
        token_id = 505

        env = {
            "algod_token_testnet": "token",
            "algod_address_testnet": "address",
            "rewards_token_id_testnet": token_id,
        }

        mocked_env = mocker.patch(
            "contract.network.environment_variables", return_value=env
        )

        client = mocker.MagicMock()
        mocked_client = mocker.patch(
            "contract.network.AlgodClient", return_value=client
        )

        stub_contract = mocker.MagicMock()
        stub_contract.get_method_by_name.return_value = "METHOD_OBJ"

        atc_stub = {
            "app_id": 555,
            "contract": stub_contract,
            "sender": "sender_address",
            "sp": mocker.MagicMock(),
            "signer": mocker.MagicMock(),
        }

        mocked_atc_stub = mocker.patch(
            "contract.network.atc_method_stub", return_value=atc_stub
        )

        atc = mocker.MagicMock()
        mocked_atc = mocker.patch(
            "contract.network.AtomicTransactionComposer", return_value=atc
        )

        response = mocker.MagicMock()
        response.tx_ids = ["TX123"]
        atc.execute.return_value = response

        mocker.patch("builtins.print")  # Silence logs

        add_allocations(network, addresses, amounts)

        mocked_env.assert_called_once_with()
        mocked_client.assert_called_once_with("token", "address")
        mocked_atc_stub.assert_called_once_with(client, network)
        mocked_atc.assert_called_once_with()

        atc.add_method_call.assert_called_once_with(
            app_id=555,
            method="METHOD_OBJ",
            sender="sender_address",
            sp=atc_stub["sp"],
            signer=atc_stub["signer"],
            method_args=[addresses, amounts],
            foreign_assets=[token_id],
        )

        atc.execute.assert_called_once_with(client, 2)

    # # create_app
    def test_contract_network_create_app_calls_wait_and_returns_app_id(self, mocker):
        client = mocker.MagicMock()
        private_key = mocker.MagicMock()
        approval_program = mocker.MagicMock()
        clear_program = mocker.MagicMock()
        contract_json = mocker.MagicMock()

        sender_address = mocker.MagicMock()
        mocker.patch(
            "contract.network.address_from_private_key", return_value=sender_address
        )

        mock_txn = mocker.MagicMock()
        mock_signed = mocker.MagicMock()
        mock_signed.transaction.get_txid.return_value = "txid123"
        mocker.patch(
            "contract.network.transaction.ApplicationCreateTxn", return_value=mock_txn
        )
        mock_txn.sign.return_value = mock_signed

        mocked_wait = mocker.patch("contract.network.wait_for_confirmation")
        client.pending_transaction_info.return_value = {"application-index": 99}
        mock_params = mocker.MagicMock()
        mock_params.gh = b"genesis_hash_value"
        client.suggested_params.return_value = mock_params

        returned_app_id, returned_genesis_hash = create_app(
            client, private_key, approval_program, clear_program, contract_json
        )

        assert returned_app_id == 99
        assert returned_genesis_hash == b"genesis_hash_value"
        mock_txn.sign.assert_called_once_with(private_key)
        client.send_transactions.assert_called_once_with([mock_signed])
        mocked_wait.assert_called_once_with(client, "txid123")

    # # delete_app
    def test_contract_network_delete_app_calls_wait(self, mocker):
        client = mocker.MagicMock()
        private_key = mocker.MagicMock()
        index = 2000

        sender_address = mocker.MagicMock()
        mocker.patch(
            "contract.network.address_from_private_key", return_value=sender_address
        )

        mock_txn = mocker.MagicMock()
        mock_signed = mocker.MagicMock()
        mock_signed.transaction.get_txid.return_value = "txid123"
        mocker.patch(
            "contract.network.transaction.ApplicationDeleteTxn", return_value=mock_txn
        )
        mock_txn.sign.return_value = mock_signed

        mocked_wait = mocker.patch("contract.network.wait_for_confirmation")

        client.pending_transaction_info.return_value = {"txn": {"txn": {"apid": index}}}

        delete_app(client, private_key, index)

        mock_txn.sign.assert_called_once_with(private_key)
        client.send_transactions.assert_called_once_with([mock_signed])
        mocked_wait.assert_called_once_with(client, "txid123")

    # # fund_app
    def test_contract_network_fund_app_for_provided_amount(self, mocker):
        app_id = 5059
        network = "testnet"
        amount = 500_000

        env = {
            "algod_token_testnet": "token",
            "algod_address_testnet": "address",
            "creator_mnemonic_testnet": "mnemonic",
        }

        mocked_env = mocker.patch(
            "contract.network.environment_variables", return_value=env
        )

        client = mocker.MagicMock()
        mocked_client = mocker.patch(
            "contract.network.AlgodClient", return_value=client
        )

        creator_private_key = mocker.MagicMock()
        mocked_private_key = mocker.patch(
            "contract.network.private_key_from_mnemonic",
            return_value=creator_private_key,
        )

        sender = "sender-address"
        mocked_address = mocker.patch(
            "contract.network.address_from_private_key",
            return_value=sender,
        )

        app_address = "app-escrow-address"
        mocked_app_address = mocker.patch(
            "contract.network.get_application_address", return_value=app_address
        )

        suggested_params = mocker.MagicMock()
        client.suggested_params.return_value = suggested_params

        mock_tx = mocker.MagicMock()
        mock_signed = mocker.MagicMock()
        mock_signed.transaction.get_txid.return_value = "tx123"

        mocked_payment = mocker.patch(
            "contract.network.PaymentTxn", return_value=mock_tx
        )
        mock_tx.sign.return_value = mock_signed

        mocked_wait = mocker.patch("contract.network.wait_for_confirmation")
        mocker.patch("builtins.print")  # suppress output

        fund_app(app_id, network, amount=amount)

        mocked_env.assert_called_once_with()
        mocked_client.assert_called_once_with("token", "address")
        mocked_private_key.assert_called_once_with("mnemonic")
        mocked_address.assert_called_once_with(creator_private_key)
        mocked_app_address.assert_called_once_with(app_id)

        mocked_payment.assert_called_once_with(
            sender=sender,
            sp=suggested_params,
            receiver=app_address,
            amt=amount,
        )

        client.send_transactions.assert_called_once_with([mock_signed])
        mocked_wait.assert_called_once_with(client, "tx123")

    def test_contract_network_fund_app_functionality(self, mocker):
        app_id = 5059
        network = "testnet"

        env = {
            "algod_token_testnet": "token",
            "algod_address_testnet": "address",
            "creator_mnemonic_testnet": "mnemonic",
        }

        mocked_env = mocker.patch(
            "contract.network.environment_variables", return_value=env
        )

        client = mocker.MagicMock()
        mocked_client = mocker.patch(
            "contract.network.AlgodClient", return_value=client
        )

        creator_private_key = mocker.MagicMock()
        mocked_private_key = mocker.patch(
            "contract.network.private_key_from_mnemonic",
            return_value=creator_private_key,
        )

        sender = "sender-address"
        mocked_address = mocker.patch(
            "contract.network.address_from_private_key",
            return_value=sender,
        )

        app_address = "app-escrow-address"
        mocked_app_address = mocker.patch(
            "contract.network.get_application_address", return_value=app_address
        )

        suggested_params = mocker.MagicMock()
        client.suggested_params.return_value = suggested_params

        mock_tx = mocker.MagicMock()
        mock_signed = mocker.MagicMock()
        mock_signed.transaction.get_txid.return_value = "tx123"

        mocked_payment = mocker.patch(
            "contract.network.PaymentTxn", return_value=mock_tx
        )
        mock_tx.sign.return_value = mock_signed

        mocked_wait = mocker.patch("contract.network.wait_for_confirmation")
        mocker.patch("builtins.print")  # suppress output

        fund_app(app_id, network)

        mocked_env.assert_called_once_with()
        mocked_client.assert_called_once_with("token", "address")
        mocked_private_key.assert_called_once_with("mnemonic")
        mocked_address.assert_called_once_with(creator_private_key)
        mocked_app_address.assert_called_once_with(app_id)

        mocked_payment.assert_called_once_with(
            sender=sender,
            sp=suggested_params,
            receiver=app_address,
            amt=100000,
        )

        client.send_transactions.assert_called_once_with([mock_signed])
        mocked_wait.assert_called_once_with(client, "tx123")

    # # reclaim_allocation
    def test_contract_network_reclaim_allocation_functionality(self, mocker):
        network = "mainnet"
        user_address = "USER123"
        token_id = 507

        env = {
            "algod_token_mainnet": "main_token",
            "algod_address_mainnet": "main_address",
            "rewards_token_id_mainnet": token_id,
        }

        mocked_env = mocker.patch(
            "contract.network.environment_variables", return_value=env
        )

        client = mocker.MagicMock()
        mocked_client = mocker.patch(
            "contract.network.AlgodClient", return_value=client
        )

        stub_contract = mocker.MagicMock()
        stub_contract.get_method_by_name.return_value = "METHOD_OBJ"

        atc_stub = {
            "app_id": 222,
            "contract": stub_contract,
            "sender": "sender_address",
            "sp": mocker.MagicMock(),
            "signer": mocker.MagicMock(),
        }

        mocked_atc_stub = mocker.patch(
            "contract.network.atc_method_stub", return_value=atc_stub
        )

        atc = mocker.MagicMock()
        mocked_atc = mocker.patch(
            "contract.network.AtomicTransactionComposer", return_value=atc
        )

        response = mocker.MagicMock()
        response.tx_ids = ["TX777"]
        atc.execute.return_value = response

        mocker.patch("builtins.print")  # Silence logs

        reclaim_allocation(network, user_address)

        mocked_env.assert_called_once_with()
        mocked_client.assert_called_once_with("main_token", "main_address")
        mocked_atc_stub.assert_called_once_with(client, network)
        mocked_atc.assert_called_once_with()

        atc.add_method_call.assert_called_once_with(
            app_id=222,
            method="METHOD_OBJ",
            sender="sender_address",
            sp=atc_stub["sp"],
            signer=atc_stub["signer"],
            method_args=[user_address],
            foreign_assets=[token_id],
        )

        atc.execute.assert_called_once_with(client, 2)
