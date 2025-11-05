"""Testing module for :py:mod:`contract.network` module."""

from contract.network import create_app, delete_app


class TestContractNetworkFunctions:
    """Testing class for :py:mod:`contract.network` functions."""

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

        returned = create_app(
            client, private_key, approval_program, clear_program, contract_json
        )

        assert returned == 99
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
