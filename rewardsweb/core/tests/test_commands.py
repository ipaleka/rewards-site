"""Testing module for :py:mod:`core.management.commands` module."""

from unittest import mock

from django.core.management import call_command


class TestExcel2CsvCommand:
    """Testing class for management command

    :py:mod:`core.management.commands.excel2csv`."""

    def test_excel2csv_command_output_for_default_values(self, mocker):
        mocked_convert = mocker.patch(
            "core.management.commands.excel2csv.convert_and_clean_excel"
        )
        with mock.patch(
            "django.core.management.base.OutputWrapper.write"
        ) as output_log:
            call_command("excel2csv")
            output_log.assert_called_once()
            output_log.assert_called_with(
                "CSV successfully exported into contributions.csv file!"
            )
        mocked_convert.assert_called_once()
        mocked_convert.assert_called_with(
            "contributions.xlsx", "contributions.csv", "legacy_contributions.csv"
        )

    def test_excel2csv_command_output_for_provided_arguments(self, mocker):
        mocked_convert = mocker.patch(
            "core.management.commands.excel2csv.convert_and_clean_excel"
        )
        input_file, output_file, legacy_file = (
            "input_file",
            "output_file",
            "legacy_file",
        )
        with mock.patch(
            "django.core.management.base.OutputWrapper.write"
        ) as output_log:
            call_command(
                "excel2csv", input=input_file, output=output_file, legacy=legacy_file
            )
            output_log.assert_called_once()
            output_log.assert_called_with(
                f"CSV successfully exported into {output_file} file!"
            )
        mocked_convert.assert_called_once()
        mocked_convert.assert_called_with(input_file, output_file, legacy_file)
