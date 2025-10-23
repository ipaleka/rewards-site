"""Testing module for :py:mod:`core.management.commands` module."""

from pathlib import Path
from unittest import mock

from django.conf import settings
from django.core.management import call_command


class TestExcel2DbCommand:
    """Testing class for management command

    :py:mod:`core.management.commands.excel2db`."""

    def test_excel2db_command_output_for_default_values(self, mocker):
        mocked_convert = mocker.patch(
            "core.management.commands.excel2db.convert_and_clean_excel"
        )
        mocked_import = mocker.patch(
            "core.management.commands.excel2db.import_from_csv", return_value=False
        )
        mocked_map = mocker.patch(
            "core.management.commands.excel2db.map_github_issues", return_value=False
        )
        with mock.patch(
            "django.core.management.base.OutputWrapper.write"
        ) as output_log:
            call_command("excel2db")
            calls = [
                mocker.call("CSV successfully exported into contributions.csv file!"),
                mocker.call("Records successfully imported!"),
                mocker.call("Issues successfully mapped!"),
            ]
            output_log.assert_has_calls(calls, any_order=True)
            assert output_log.call_count == 3

        fixtures_dir = settings.BASE_DIR.parent / "fixtures"
        mocked_convert.assert_called_once_with(
            fixtures_dir / "contributions.xlsx",
            fixtures_dir / "contributions.csv",
            fixtures_dir / "legacy_contributions.csv",
        )
        mocked_import.assert_called_once_with(
            fixtures_dir / "contributions.csv",
            fixtures_dir / "legacy_contributions.csv",
        )
        mocked_map.assert_called_once_with(github_token="")

    def test_excel2db_command_output_for_default_values_on_import_response(
        self, mocker
    ):
        mocked_convert = mocker.patch(
            "core.management.commands.excel2db.convert_and_clean_excel"
        )
        response = "response"
        mocked_import = mocker.patch(
            "core.management.commands.excel2db.import_from_csv", return_value=response
        )
        mocked_map = mocker.patch("core.management.commands.excel2db.map_github_issues")
        with mock.patch(
            "django.core.management.base.OutputWrapper.write"
        ) as output_log:
            call_command("excel2db")
            calls = [
                mocker.call("CSV successfully exported into contributions.csv file!"),
                mocker.call(response),
            ]
            output_log.assert_has_calls(calls, any_order=True)
            assert output_log.call_count == 2

        fixtures_dir = settings.BASE_DIR.parent / "fixtures"
        mocked_convert.assert_called_once_with(
            fixtures_dir / "contributions.xlsx",
            fixtures_dir / "contributions.csv",
            fixtures_dir / "legacy_contributions.csv",
        )
        mocked_import.assert_called_once_with(
            fixtures_dir / "contributions.csv",
            fixtures_dir / "legacy_contributions.csv",
        )
        mocked_map.assert_not_called()

    def test_excel2db_command_output_for_default_values_on_mapping_response(
        self, mocker
    ):
        mocked_convert = mocker.patch(
            "core.management.commands.excel2db.convert_and_clean_excel"
        )
        response = "response2"
        mocked_import = mocker.patch(
            "core.management.commands.excel2db.import_from_csv", return_value=False
        )
        mocked_map = mocker.patch(
            "core.management.commands.excel2db.map_github_issues",
            return_value=response,
        )
        with mock.patch(
            "django.core.management.base.OutputWrapper.write"
        ) as output_log:
            call_command("excel2db")
            calls = [
                mocker.call("CSV successfully exported into contributions.csv file!"),
                mocker.call("Records successfully imported!"),
                mocker.call(response),
            ]
            output_log.assert_has_calls(calls, any_order=True)
            assert output_log.call_count == 3

        fixtures_dir = settings.BASE_DIR.parent / "fixtures"
        mocked_convert.assert_called_once_with(
            fixtures_dir / "contributions.xlsx",
            fixtures_dir / "contributions.csv",
            fixtures_dir / "legacy_contributions.csv",
        )
        mocked_import.assert_called_once_with(
            fixtures_dir / "contributions.csv",
            fixtures_dir / "legacy_contributions.csv",
        )
        mocked_map.assert_called_once_with(github_token="")

    def test_excel2db_command_output_for_provided_arguments(self, mocker):
        mocked_convert = mocker.patch(
            "core.management.commands.excel2db.convert_and_clean_excel"
        )
        mocked_import = mocker.patch(
            "core.management.commands.excel2db.import_from_csv", return_value=False
        )
        mocked_map = mocker.patch(
            "core.management.commands.excel2db.map_github_issues", return_value=False
        )
        input_file, output_file, legacy_file, token = (
            "input_file",
            "output_file",
            "legacy_file",
            "token",
        )
        with mock.patch(
            "django.core.management.base.OutputWrapper.write"
        ) as output_log:
            call_command(
                "excel2db",
                input=input_file,
                output=output_file,
                legacy=legacy_file,
                token=token,
            )
            calls = [
                mocker.call(f"CSV successfully exported into {output_file} file!"),
                mocker.call("Records successfully imported!"),
                mocker.call("Issues successfully mapped!"),
            ]
            output_log.assert_has_calls(calls, any_order=True)
            assert output_log.call_count == 3
        mocked_convert.assert_called_once_with(
            Path(input_file), Path(output_file), Path(legacy_file)
        )
        mocked_import.assert_called_once_with(Path(output_file), Path(legacy_file))
        mocked_map.assert_called_once_with(github_token=token)
