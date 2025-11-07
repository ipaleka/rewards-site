"""Django management command for deploying Rewards smart contract to blockchain."""

from django.core.management.base import BaseCommand

from contract.deploy import deploy_and_setup


class Command(BaseCommand):
    help = "Call smart contract's deployment function to deploy it on blockchain."

    def add_arguments(self, parser):
        """Add optional network argument to command."""
        parser.add_argument("network", type=str, nargs="?", default="")

    def handle(self, *args, **options):
        """Call smart contract's deployment function to deploy it on blockchain.

        :var network: blockchain network to create application on (testnet or mainnet)
        :type network: str
        :var app_id: created application's unique identifier
        :type app_id: int
        """
        network = options.get("network") or "testnet"
        app_id = deploy_and_setup(network)
        self.stdout.write(
            "Application %i successfully deployed on %s!" % (app_id, network)
        )
