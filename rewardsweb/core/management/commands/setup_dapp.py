"""Django management command for Rewards smart contract setup."""

from django.core.management.base import BaseCommand

from contract.deploy import setup_app


class Command(BaseCommand):
    help = (
        "Call Rewards dApp's setup function to define rewards token and claim period."
    )

    def add_arguments(self, parser):
        """Add optional network argument to command."""
        parser.add_argument("network", type=str, nargs="?", default="")

    def handle(self, *args, **options):
        """Call Rewards dApp's setup function to define rewards token and claim period.

        :var network: blockchain network to setup application on (testnet or mainnet)
        :type network: str
        :var token_id: configured ASA (Algorand Standard Asset) ID
        :type token_id: int
        :var claim_period_duration: configured claim period duration
        :type claim_period_duration: int
        """
        network = options.get("network") or "testnet"
        token_id, claim_period_duration = setup_app(network)
        self.stdout.write(
            "Application was set up for token %i and claim duration of %i days!"
            % (token_id, int(claim_period_duration / 86400))
        )
