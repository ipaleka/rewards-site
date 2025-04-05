"""Django management command for NFT purchases data retrieving."""

import time

from django.core.management.base import BaseCommand

from utils.csv_from_excel import convert_and_clean_excel


class Command(BaseCommand):
    help = "Calls script which converts Excel file to CSV."

    def add_arguments(self, parser):
        """Add optional input_file and output files arguments to command."""
        parser.add_argument("input", type=str, nargs="?", default="")
        parser.add_argument("output", type=str, nargs="?", default="")
        parser.add_argument("legacy", type=str, nargs="?", default="")

    def handle(self, *args, **options):
        """Call `convert_and_clean_excel` script to export Excel file to CSV."""
        input_file = options.get("input") or "contributions.xlsx"
        output_file = options.get("output") or "contributions.csv"
        legacy_file = options.get("legacy") or "legacy_contributions.csv"

        a = time.time()
        convert_and_clean_excel(input_file, output_file, legacy_file)
        self.stdout.write("CSV successfully exported into %s file!" % (output_file,))
        print(time.time() - a)
