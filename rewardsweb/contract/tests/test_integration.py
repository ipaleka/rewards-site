"""Testing module for :py:mod:`contract.contract` module."""

import json
import os
import time
from pathlib import Path

import pytest
from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    Arc56Contract,
    AssetTransferParams,
    LogicError,
    PaymentParams,
    SendParams,
    SigningAccount,
)
from algokit_utils.applications import (
    AppClient,
    AppClientMethodCallParams,
    AppClientParams,
)
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    TransactionWithSigner,
)
from algosdk.error import AlgodHTTPError
from algosdk.transaction import AssetCreateTxn
from dotenv import load_dotenv

from contract.helpers import compile_program
from contract.network import create_app

load_dotenv(Path(__file__).parent.parent / ".env")

dapp_name = os.getenv("REWARDS_DAPP_NAME")

# Assume tests are run from the project root
CONTRACT_PATH = Path(__file__).parent.parent / "artifacts"
APP_SPEC_PATH = CONTRACT_PATH / f"{dapp_name}.arc56.json"


@pytest.fixture(scope="session")
def app_spec() -> Arc56Contract:
    """Get the application specification from the compiled artifact."""
    spec = json.loads(APP_SPEC_PATH.read_text())
    for network in spec["networks"].values():
        if "appID" in network:
            network["appId"] = network.pop("appID")
    return Arc56Contract.from_dict(spec)


def _create_asset(algorand_client: AlgorandClient, account: SigningAccount) -> int:
    """Create a new asset for testing."""
    sp = algorand_client.client.algod.suggested_params()
    atc = AtomicTransactionComposer()
    atc.add_transaction(
        TransactionWithSigner(
            AssetCreateTxn(
                asset_name="ASA Stats Token test",
                unit_name="ASASTATS",
                sender=account.address,
                sp=sp,
                total=1_000_000_000_000_000,
                decimals=6,
                default_frozen=False,
            ),
            signer=account.signer,
        )
    )
    result = atc.execute(algorand_client.client.algod, 4)
    tx_info = algorand_client.client.algod.pending_transaction_info(result.tx_ids[0])
    return tx_info["asset-index"]


def _make_transfer(asset_creator_account, receiver, token_id, amount):
    algorand = AlgorandClient.from_environment()
    algorand.send.asset_transfer(
        AssetTransferParams(
            sender=asset_creator_account.address,
            asset_id=token_id,
            amount=amount,
            receiver=receiver,
            signer=asset_creator_account.signer,
        ),
        SendParams(max_rounds_to_wait_for_confirmation=5, suppress_log=False),
    )


class BaseTestContract:
    """Base testing class for :class:`contract.contract.Rewards`."""

    name = "rewards"
    claim_period_duration = 3600

    @pytest.fixture(autouse=True)
    def _setup_contract(
        self,
        algorand_client: AlgorandClient,
        app_spec: Arc56Contract,
        token_id: int,
        admin_account: SigningAccount,
    ):
        """
        Deploy app using app_spec + your own TEAL compile logic.
        """

        algod = algorand_client.client.algod

        # --------------------------------------------------------------------
        # ✅ Extract name from app_spec (this matches *.approval.teal filenames)
        # --------------------------------------------------------------------
        dapp_name = app_spec.name  # <-- this IS from app_spec

        artifacts_path = Path(__file__).resolve().parent.parent / "artifacts"

        approval_teal_path = artifacts_path / f"{dapp_name}.approval.teal"
        clear_teal_path = artifacts_path / f"{dapp_name}.clear.teal"

        # --------------------------------------------------------------------
        # ✅ Load TEAL source from artifacts (using your logic)
        # --------------------------------------------------------------------
        approval_program_source = approval_teal_path.read_bytes()
        clear_program_source = clear_teal_path.read_bytes()

        # --------------------------------------------------------------------
        # ✅ Compile using your compile_program()
        # --------------------------------------------------------------------
        approval_program = compile_program(algod, approval_program_source)
        clear_program = compile_program(algod, clear_program_source)

        # --------------------------------------------------------------------
        # ✅ app_spec → ARC56 JSON (your create_app expects dict)
        # --------------------------------------------------------------------
        contract_json = json.loads(app_spec.to_json())

        # --------------------------------------------------------------------
        # ✅ Create the app using your create_app() function
        #    This triggers @baremethod(create="require")
        # --------------------------------------------------------------------
        app_id, _gh = create_app(
            client=algod,
            private_key=admin_account.private_key,
            approval_program=approval_program,
            clear_program=clear_program,
            contract_json=contract_json,
        )

        # --------------------------------------------------------------------
        # ✅ Wrap in AppClient for ABI calls
        # --------------------------------------------------------------------
        rewards_client = AppClient(
            AppClientParams(
                algorand=algorand_client,
                app_spec=app_spec,
                app_id=app_id,
            )
        )

        # --------------------------------------------------------------------
        # ✅ Fund the contract account so inner ASA transfers work
        # --------------------------------------------------------------------
        algorand_client.send.payment(
            PaymentParams(
                sender=admin_account.address,
                receiver=rewards_client.app_address,
                amount=AlgoAmount(algo=1),
                signer=admin_account.signer,
            )
        )

        # --------------------------------------------------------------------
        # ✅ Call setup(token_id, claim_period_duration)
        # --------------------------------------------------------------------
        rewards_client.send.call(
            AppClientMethodCallParams(
                method="setup",
                args=[token_id, self.claim_period_duration],
                sender=admin_account.address,
                signer=admin_account.signer,
                static_fee=AlgoAmount(micro_algo=2000),
            )
        )

        # Expose for tests (test methods can now reference self.rewards_client)
        self.rewards_client = rewards_client

    @pytest.fixture
    def algorand_client(self) -> AlgorandClient:
        return AlgorandClient.from_environment()

    @pytest.fixture
    def admin_account(self, algorand_client: AlgorandClient) -> SigningAccount:
        return algorand_client.account.from_environment(
            "ADMIN_ACCOUNT" + "_" + self.name.upper(), fund_with=AlgoAmount(algo=1000)
        )

    @pytest.fixture
    def asset_creator_account(self, algorand_client: AlgorandClient) -> SigningAccount:
        return algorand_client.account.from_environment(
            "ASSET_CREATOR_ACCOUNT" + "_" + self.name.upper(),
            fund_with=AlgoAmount(algo=100),
        )

    @pytest.fixture
    def token_id(
        self, algorand_client: AlgorandClient, asset_creator_account: SigningAccount
    ) -> int:
        return _create_asset(algorand_client, asset_creator_account)

    @pytest.fixture
    def user_account(self, algorand_client: AlgorandClient) -> SigningAccount:
        return algorand_client.account.from_environment(
            "USER_ACCOUNT" + "_" + self.name.upper(),
            fund_with=AlgoAmount(algo=10),
        )


class TestContractAddAllocations(BaseTestContract):
    """Testing class for :class:`contract.contract.Rewards` add_allocations method."""

    name = "add"

    @pytest.fixture
    def other_account(self, algorand_client: AlgorandClient) -> SigningAccount:
        return algorand_client.account.from_environment(
            "OTHER_ACCOUNT" + "_" + self.name.upper(),
            fund_with=AlgoAmount(algo=10),
        )

    @pytest.fixture
    def user_accounts_4(self, algorand_client: AlgorandClient) -> SigningAccount:
        users_count = 4
        user_accounts = []
        for i in range(users_count):
            user_accounts.append(
                algorand_client.account.from_environment(
                    f"USER{i}_ACCOUNT", fund_with=AlgoAmount(algo=10)
                )
            )
        return user_accounts

    @pytest.fixture
    def user_accounts_5(self, algorand_client: AlgorandClient) -> SigningAccount:
        users_count = 5
        user_accounts = []
        for i in range(users_count):
            user_accounts.append(
                algorand_client.account.from_environment(
                    f"USER{i}_ACCOUNT", fund_with=AlgoAmount(algo=10)
                )
            )
        return user_accounts

    def test_contract_rewards_add_alocations_for_no_admin(
        self,
        asset_creator_account: SigningAccount,
        token_id: int,
        other_account: SigningAccount,
        user_account: SigningAccount,
    ) -> None:
        amount = 1_000_000_000

        with pytest.raises(LogicError, match="Sender is not the admin"):
            (
                self.rewards_client.algorand.new_group()
                .add_asset_transfer(
                    AssetTransferParams(
                        sender=asset_creator_account.address,
                        asset_id=token_id,
                        receiver=self.rewards_client.app_address,
                        amount=amount,
                        signer=asset_creator_account.signer,
                    )
                )
                .add_app_call_method_call(
                    self.rewards_client.params.call(
                        AppClientMethodCallParams(
                            method="add_allocations",
                            args=[[user_account.address], [amount, amount]],
                            sender=other_account.address,
                            signer=other_account.signer,
                            box_references=[user_account.address.encode()],
                            static_fee=AlgoAmount(micro_algo=2000),
                        )
                    )
                )
                .send(SendParams(cover_app_call_inner_transaction_fees=True))
            )

    def test_contract_rewards_add_alocations_different_sizes(
        self,
        admin_account: SigningAccount,
        asset_creator_account: SigningAccount,
        token_id: int,
        user_account: SigningAccount,
    ) -> None:
        amount = 1_000_000_000

        with pytest.raises(LogicError, match="Input arrays must have the same length"):
            (
                self.rewards_client.algorand.new_group()
                .add_asset_transfer(
                    AssetTransferParams(
                        sender=asset_creator_account.address,
                        asset_id=token_id,
                        receiver=self.rewards_client.app_address,
                        amount=amount,
                        signer=asset_creator_account.signer,
                    )
                )
                .add_app_call_method_call(
                    self.rewards_client.params.call(
                        AppClientMethodCallParams(
                            method="add_allocations",
                            args=[[user_account.address], [amount, amount]],
                            sender=admin_account.address,
                            signer=admin_account.signer,
                            box_references=[user_account.address.encode()],
                            static_fee=AlgoAmount(micro_algo=2000),
                        )
                    )
                )
                .send(SendParams(cover_app_call_inner_transaction_fees=True))
            )

    def test_contract_rewards_add_alocations_single_address(
        self,
        admin_account: SigningAccount,
        asset_creator_account: SigningAccount,
        token_id: int,
        user_account: SigningAccount,
    ) -> None:
        amount = 1_000_000_000

        (
            self.rewards_client.algorand.new_group()
            .add_asset_transfer(
                AssetTransferParams(
                    sender=asset_creator_account.address,
                    asset_id=token_id,
                    receiver=self.rewards_client.app_address,
                    amount=amount,
                    signer=asset_creator_account.signer,
                )
            )
            .add_app_call_method_call(
                self.rewards_client.params.call(
                    AppClientMethodCallParams(
                        method="add_allocations",
                        args=[[user_account.address], [amount]],
                        sender=admin_account.address,
                        signer=admin_account.signer,
                        box_references=[user_account.address.encode()],
                        static_fee=AlgoAmount(micro_algo=2000),
                    )
                )
            )
            .send(SendParams(cover_app_call_inner_transaction_fees=True))
        )

    def test_contract_rewards_add_alocations_multiple_four_addresses(
        self,
        admin_account: SigningAccount,
        asset_creator_account: SigningAccount,
        token_id: int,
        user_accounts_4: list,
    ) -> None:
        amount = 1_000_000_000

        (
            self.rewards_client.algorand.new_group()
            .add_asset_transfer(
                AssetTransferParams(
                    sender=asset_creator_account.address,
                    asset_id=token_id,
                    receiver=self.rewards_client.app_address,
                    amount=amount * len(user_accounts_4),
                    signer=asset_creator_account.signer,
                )
            )
            .add_app_call_method_call(
                self.rewards_client.params.call(
                    AppClientMethodCallParams(
                        method="add_allocations",
                        args=[
                            [user_account.address for user_account in user_accounts_4],
                            [amount] * len(user_accounts_4),
                        ],
                        sender=admin_account.address,
                        signer=admin_account.signer,
                        box_references=[
                            user_account.address.encode()
                            for user_account in user_accounts_4
                        ],
                        static_fee=AlgoAmount(micro_algo=2000),
                    )
                )
            )
            .send(SendParams(cover_app_call_inner_transaction_fees=True))
        )

    def test_contract_rewards_add_alocations_extended_five_addresses(
        self,
        admin_account: SigningAccount,
        asset_creator_account: SigningAccount,
        token_id: int,
        user_accounts_5: list,
    ) -> None:
        amount = 1_000_000_000

        with pytest.raises(
            ValueError,
            match=(
                "No more transactions below reference limit. "
                "Add another app call to the group."
            ),
        ):
            (
                self.rewards_client.algorand.new_group()
                .add_asset_transfer(
                    AssetTransferParams(
                        sender=asset_creator_account.address,
                        asset_id=token_id,
                        receiver=self.rewards_client.app_address,
                        amount=amount * len(user_accounts_5),
                        signer=asset_creator_account.signer,
                    )
                )
                .add_app_call_method_call(
                    self.rewards_client.params.call(
                        AppClientMethodCallParams(
                            method="add_allocations",
                            args=[
                                [
                                    user_account.address
                                    for user_account in user_accounts_5
                                ],
                                [amount] * len(user_accounts_5),
                            ],
                            sender=admin_account.address,
                            signer=admin_account.signer,
                            box_references=[
                                user_account.address.encode()
                                for user_account in user_accounts_5
                            ],
                            static_fee=AlgoAmount(micro_algo=2000),
                        )
                    )
                )
                .send(SendParams(cover_app_call_inner_transaction_fees=True))
            )


class TestContractClaim(BaseTestContract):
    """Testing class for :class:`contract.contract.Rewards` claim method."""

    name = "claim"

    def test_contract_rewards_claim_non_opted_in_user(
        self,
        admin_account: SigningAccount,
        asset_creator_account: SigningAccount,
        token_id: int,
        user_account: SigningAccount,
    ) -> None:
        amount = 1_000_000_000

        _make_transfer(
            asset_creator_account, self.rewards_client.app_address, token_id, amount
        )

        (
            self.rewards_client.algorand.new_group()
            .add_asset_transfer(
                AssetTransferParams(
                    sender=asset_creator_account.address,
                    asset_id=token_id,
                    receiver=self.rewards_client.app_address,
                    amount=amount,
                    signer=asset_creator_account.signer,
                )
            )
            .add_app_call_method_call(
                self.rewards_client.params.call(
                    AppClientMethodCallParams(
                        method="add_allocations",
                        args=[[user_account.address], [amount]],
                        sender=admin_account.address,
                        signer=admin_account.signer,
                        box_references=[user_account.address.encode()],
                        static_fee=AlgoAmount(micro_algo=2000),
                    )
                )
            )
            .send(SendParams(cover_app_call_inner_transaction_fees=True))
        )

        with pytest.raises(LogicError, match="Sender has not opted-in to the asset"):
            self.rewards_client.send.call(
                AppClientMethodCallParams(
                    method="claim",
                    sender=user_account.address,
                    signer=user_account.signer,
                    box_references=[user_account.address.encode()],
                    static_fee=AlgoAmount(micro_algo=2000),
                    asset_references=[token_id],
                )
            )

    def test_contract_rewards_claim_opted_in_user(
        self,
        admin_account: SigningAccount,
        asset_creator_account: SigningAccount,
        token_id: int,
        user_account: SigningAccount,
    ) -> None:
        amount = 1_000_000_000

        _make_transfer(
            asset_creator_account, self.rewards_client.app_address, token_id, amount
        )

        # User opts into the asset
        self.rewards_client.algorand.send.asset_opt_in(
            AssetTransferParams(
                sender=user_account.address,
                asset_id=token_id,
                amount=0,
                receiver=user_account.address,
                signer=user_account.signer,
            )
        )

        (
            self.rewards_client.algorand.new_group()
            .add_asset_transfer(
                AssetTransferParams(
                    sender=asset_creator_account.address,
                    asset_id=token_id,
                    receiver=self.rewards_client.app_address,
                    amount=amount,
                    signer=asset_creator_account.signer,
                )
            )
            .add_app_call_method_call(
                self.rewards_client.params.call(
                    AppClientMethodCallParams(
                        method="add_allocations",
                        args=[[user_account.address], [amount]],
                        sender=admin_account.address,
                        signer=admin_account.signer,
                        box_references=[user_account.address.encode()],
                        static_fee=AlgoAmount(micro_algo=2000),
                    )
                )
            )
            .send(SendParams(cover_app_call_inner_transaction_fees=True))
        )
        self.rewards_client.send.call(
            AppClientMethodCallParams(
                method="claim",
                sender=user_account.address,
                signer=user_account.signer,
                box_references=[user_account.address.encode()],
                static_fee=AlgoAmount(micro_algo=2000),
                asset_references=[token_id],
            )
        )

        # Verify the user received the asset
        user_asset_info = self.rewards_client.algorand.client.algod.account_asset_info(
            user_account.address, token_id
        )
        assert user_asset_info["asset-holding"]["amount"] == amount

        with pytest.raises(AlgodHTTPError, match="box not found"):
            self.rewards_client.algorand.client.algod.application_box_by_name(
                self.rewards_client.app_id, user_account.address.encode()
            )


class TestContractReclaimAllocations(BaseTestContract):
    """Testing class for :class:`contract.contract.Rewards` reclaim_allocations."""

    name = "reclaim"

    def test_contract_rewards_reclaim_allocations_before_expiry_fails(
        self,
        admin_account: SigningAccount,
        asset_creator_account: SigningAccount,
        token_id: int,
        user_account: SigningAccount,
    ) -> None:
        amount = 1_000_000_000

        (
            self.rewards_client.algorand.new_group()
            .add_asset_transfer(
                AssetTransferParams(
                    sender=asset_creator_account.address,
                    asset_id=token_id,
                    receiver=self.rewards_client.app_address,
                    amount=amount,
                    signer=asset_creator_account.signer,
                )
            )
            .add_app_call_method_call(
                self.rewards_client.params.call(
                    AppClientMethodCallParams(
                        method="add_allocations",
                        args=[[user_account.address], [amount]],
                        sender=admin_account.address,
                        signer=admin_account.signer,
                        box_references=[user_account.address.encode()],
                        static_fee=AlgoAmount(micro_algo=2000),
                    )
                )
            )
            .send(SendParams(cover_app_call_inner_transaction_fees=True))
        )

        with pytest.raises(LogicError, match="Claim period has not ended"):
            self.rewards_client.send.call(
                AppClientMethodCallParams(
                    method="reclaim_allocation",
                    args=[user_account.address],
                    sender=admin_account.address,
                    signer=admin_account.signer,
                    box_references=[user_account.address.encode()],
                )
            )


class TestContractReclaimAllocationsShortPeriod(BaseTestContract):
    """Testing class for :class:`contract.contract.Rewards` reclaim_allocations

    with a short claim period so we can test actual reclaiming.
    ."""

    name = "reclaim_short"
    claim_period_duration = 2

    @pytest.mark.order(1)
    def test_contract_rewards_reclaim_allocations_after_short_period(
        self,
        admin_account: SigningAccount,
        asset_creator_account: SigningAccount,
        token_id: int,
        user_account: SigningAccount,
    ) -> None:
        amount = 1_000_000_000

        (
            self.rewards_client.algorand.new_group()
            .add_asset_transfer(
                AssetTransferParams(
                    sender=asset_creator_account.address,
                    asset_id=token_id,
                    receiver=self.rewards_client.app_address,
                    amount=amount,
                    signer=asset_creator_account.signer,
                )
            )
            .add_app_call_method_call(
                self.rewards_client.params.call(
                    AppClientMethodCallParams(
                        method="add_allocations",
                        args=[[user_account.address], [amount]],
                        sender=admin_account.address,
                        signer=admin_account.signer,
                        box_references=[user_account.address.encode()],
                        static_fee=AlgoAmount(micro_algo=2000),
                    )
                )
            )
            .send(SendParams(cover_app_call_inner_transaction_fees=True))
        )

        time.sleep(self.claim_period_duration + 2)

        self.rewards_client.algorand.send.asset_opt_in(
            AssetTransferParams(
                sender=admin_account.address,
                asset_id=token_id,
                amount=0,
                receiver=admin_account.address,
                signer=admin_account.signer,
            )
        )

        self.rewards_client.send.call(
            AppClientMethodCallParams(
                method="reclaim_allocation",
                args=[user_account.address],
                sender=admin_account.address,
                signer=admin_account.signer,
                box_references=[user_account.address.encode()],
                static_fee=AlgoAmount(micro_algo=2000),
            )
        )
