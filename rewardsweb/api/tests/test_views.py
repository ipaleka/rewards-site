"""Testing module for :py:mod:`api.views` module."""

import pytest
from unittest.mock import patch, AsyncMock
from rest_framework.response import Response
from rest_framework import status
from api.views import (
    aggregated_cycle_response,
    contributions_response,
    CycleAggregatedView,
    CurrentCycleAggregatedView,
    CyclePlainView,
    CurrentCyclePlainView,
    ContributionsView,
    ContributionsTailView,
    AddContributionView,
)
from core.models import Cycle, Contributor


class TestApiViewsHelpers:
    """Testing class for :py:mod:`api.views` helper functions."""

    @pytest.mark.asyncio
    async def test_api_views_aggregated_cycle_response_with_none_cycle(self):
        response = await aggregated_cycle_response(None)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data == {"error": "Cycle not found"}

    @pytest.mark.asyncio
    async def test_api_views_aggregated_cycle_response_with_valid_cycle(self, mocker):
        mock_cycle = mocker.MagicMock(spec=Cycle)
        mock_cycle.id = 1
        mock_cycle.start = "2023-01-01"
        mock_cycle.end = "2023-01-31"
        mock_cycle.contributor_rewards = {"addr1": 100, "addr2": 200}
        mock_cycle.total_rewards = 300

        # Mock sync_to_async calls to return awaitable objects
        with patch("api.views.sync_to_async") as mock_sync_to_async:
            # Create awaitable mocks that return the expected values
            mock_contributor_rewards = AsyncMock(
                return_value={"addr1": 100, "addr2": 200}
            )
            mock_total_rewards = AsyncMock(return_value=300)
            mock_sync_to_async.side_effect = [
                mock_contributor_rewards,
                mock_total_rewards,
            ]

            # Mock serializer
            mock_serializer = mocker.MagicMock()
            mock_serializer.data = {"id": 1, "start": "2023-01-01", "end": "2023-01-31"}
            mock_serializer.is_valid.return_value = True
            with patch(
                "api.views.AggregatedCycleSerializer", return_value=mock_serializer
            ):
                response = await aggregated_cycle_response(mock_cycle)

        assert isinstance(response, Response)
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_api_views_contributions_response(self, mocker):
        mock_contributions = mocker.MagicMock()
        mock_humanized_data = [{"id": 1, "contributor_name": "test"}]

        # Mock sync_to_async to return awaitable
        with patch("api.views.sync_to_async") as mock_sync_to_async:
            mock_humanize = AsyncMock(return_value=mock_humanized_data)
            mock_sync_to_async.return_value = mock_humanize

            # Mock serializer
            mock_serializer = mocker.MagicMock()
            mock_serializer.data = mock_humanized_data
            mock_serializer.is_valid.return_value = True
            with patch(
                "api.views.HumanizedContributionSerializer",
                return_value=mock_serializer,
            ):
                response = await contributions_response(mock_contributions)

        assert isinstance(response, Response)
        assert response.status_code == status.HTTP_200_OK


class TestApiViewsCycleAggregatedView:
    """Testing class for :py:class:`api.views.CycleAggregatedView`."""

    @pytest.mark.asyncio
    async def test_api_views_cycle_aggregated_view_get_existing_cycle(self, mocker):
        view = CycleAggregatedView()
        mock_request = mocker.MagicMock()
        cycle_id = 1

        mock_cycle = mocker.MagicMock(spec=Cycle)

        # Mock sync_to_async to return awaitable that returns the cycle
        with patch("api.views.sync_to_async") as mock_sync_to_async:
            mock_db_call = AsyncMock(return_value=mock_cycle)
            mock_sync_to_async.return_value = mock_db_call

            with patch(
                "api.views.aggregated_cycle_response", new_callable=AsyncMock
            ) as mock_response:
                mock_response.return_value = Response({"id": cycle_id})

                response = await view.get(mock_request, cycle_id)

                mock_sync_to_async.assert_called_once()
                mock_response.assert_called_once_with(mock_cycle)
                assert isinstance(response, Response)

    @pytest.mark.asyncio
    async def test_api_views_cycle_aggregated_view_get_nonexistent_cycle(self, mocker):
        view = CycleAggregatedView()
        mock_request = mocker.MagicMock()
        cycle_id = 999

        # Mock sync_to_async to return awaitable that returns None
        with patch("api.views.sync_to_async") as mock_sync_to_async:
            mock_db_call = AsyncMock(return_value=None)
            mock_sync_to_async.return_value = mock_db_call

            with patch(
                "api.views.aggregated_cycle_response", new_callable=AsyncMock
            ) as mock_response:
                mock_response.return_value = Response(
                    {"error": "Cycle not found"}, status=404
                )

                response = await view.get(mock_request, cycle_id)

                mock_response.assert_called_once_with(None)
                assert isinstance(response, Response)


class TestApiViewsCurrentCycleAggregatedView:
    """Testing class for :py:class:`api.views.CurrentCycleAggregatedView`."""

    @pytest.mark.asyncio
    async def test_api_views_current_cycle_aggregated_view_get(self, mocker):
        view = CurrentCycleAggregatedView()
        mock_request = mocker.MagicMock()

        mock_cycle = mocker.MagicMock(spec=Cycle)

        # Mock sync_to_async to return awaitable
        with patch("api.views.sync_to_async") as mock_sync_to_async:
            mock_db_call = AsyncMock(return_value=mock_cycle)
            mock_sync_to_async.return_value = mock_db_call

            with patch(
                "api.views.aggregated_cycle_response", new_callable=AsyncMock
            ) as mock_response:
                mock_response.return_value = Response({"id": 1})

                response = await view.get(mock_request)

                mock_sync_to_async.assert_called_once()
                mock_response.assert_called_once_with(mock_cycle)
                assert isinstance(response, Response)


class TestApiViewsCyclePlainView:
    """Testing class for :py:class:`api.views.CyclePlainView`."""

    @pytest.mark.asyncio
    async def test_api_views_cycle_plain_view_get_existing_cycle(self, mocker):
        view = CyclePlainView()
        mock_request = mocker.MagicMock()
        cycle_id = 1

        mock_cycle = mocker.MagicMock(spec=Cycle)

        # Mock sync_to_async to return awaitable
        with patch("api.views.sync_to_async") as mock_sync_to_async:
            mock_db_call = AsyncMock(return_value=mock_cycle)
            mock_sync_to_async.return_value = mock_db_call

            with patch("api.views.CycleSerializer") as mock_serializer:
                mock_serializer_instance = mocker.MagicMock()
                mock_serializer_instance.data = {"id": cycle_id}
                mock_serializer.return_value = mock_serializer_instance

                response = await view.get(mock_request, cycle_id)

                mock_serializer.assert_called_once_with(mock_cycle)
                assert isinstance(response, Response)
                assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_api_views_cycle_plain_view_get_nonexistent_cycle(self, mocker):
        view = CyclePlainView()
        mock_request = mocker.MagicMock()
        cycle_id = 999

        # Mock sync_to_async to return awaitable that returns None
        with patch("api.views.sync_to_async") as mock_sync_to_async:
            mock_db_call = AsyncMock(return_value=None)
            mock_sync_to_async.return_value = mock_db_call

            response = await view.get(mock_request, cycle_id)

            assert isinstance(response, Response)
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert response.data == {"error": "Cycle not found"}


class TestApiViewsCurrentCyclePlainView:
    """Testing class for :py:class:`api.views.CurrentCyclePlainView`."""

    @pytest.mark.asyncio
    async def test_api_views_current_cycle_plain_view_get(self, mocker):
        view = CurrentCyclePlainView()
        mock_request = mocker.MagicMock()

        mock_cycle = mocker.MagicMock(spec=Cycle)

        # Mock sync_to_async to return awaitable
        with patch("api.views.sync_to_async") as mock_sync_to_async:
            mock_db_call = AsyncMock(return_value=mock_cycle)
            mock_sync_to_async.return_value = mock_db_call

            with patch("api.views.CycleSerializer") as mock_serializer:
                mock_serializer_instance = mocker.MagicMock()
                mock_serializer_instance.data = {"id": 1}
                mock_serializer.return_value = mock_serializer_instance

                response = await view.get(mock_request)

                mock_serializer.assert_called_once_with(mock_cycle)
                assert isinstance(response, Response)
                assert response.status_code == status.HTTP_200_OK


class TestApiViewsContributionsView:
    """Testing class for :py:class:`api.views.ContributionsView`."""

    @pytest.mark.asyncio
    async def test_api_views_contributions_view_get_with_username(self, mocker):
        view = ContributionsView()
        mock_request = mocker.MagicMock()
        mock_request.GET = mocker.MagicMock()
        mock_request.GET.get.return_value = "testuser"

        mock_contributor = mocker.MagicMock(spec=Contributor)
        mock_queryset = mocker.MagicMock()

        # Mock sync_to_async calls to return awaitables
        with patch("api.views.sync_to_async") as mock_sync_to_async:
            mock_contributor_call = AsyncMock(return_value=mock_contributor)
            mock_queryset_call = AsyncMock(return_value=mock_queryset)
            mock_sync_to_async.side_effect = [mock_contributor_call, mock_queryset_call]

            with patch("api.views.Contribution.objects") as mock_contribution_objects:
                mock_contribution_objects.filter.return_value = mock_queryset
                with patch(
                    "api.views.contributions_response", new_callable=AsyncMock
                ) as mock_response:
                    mock_response.return_value = Response([{"id": 1}])

                    response = await view.get(mock_request)

                    mock_request.GET.get.assert_called_with("name")
                    mock_contribution_objects.filter.assert_called_once_with(
                        contributor=mock_contributor
                    )
                    mock_response.assert_called_once_with(mock_queryset)
                    assert isinstance(response, Response)

    @pytest.mark.asyncio
    async def test_api_views_contributions_view_get_without_username(self, mocker):
        view = ContributionsView()
        mock_request = mocker.MagicMock()
        mock_request.GET = mocker.MagicMock()
        mock_request.GET.get.return_value = None

        mock_queryset = mocker.MagicMock()

        # Mock sync_to_async to return awaitable
        with patch("api.views.sync_to_async") as mock_sync_to_async:
            mock_db_call = AsyncMock(return_value=mock_queryset)
            mock_sync_to_async.return_value = mock_db_call

            with patch("api.views.Contribution.objects") as mock_contribution_objects:
                # Mock the chain: objects.order_by().__getitem__()
                mock_order_by = mocker.MagicMock()
                mock_order_by.__getitem__.return_value = mock_queryset
                mock_contribution_objects.order_by.return_value = mock_order_by

                with patch(
                    "api.views.contributions_response", new_callable=AsyncMock
                ) as mock_response:
                    mock_response.return_value = Response([{"id": 1}])

                    response = await view.get(mock_request)

                    mock_request.GET.get.assert_called_with("name")
                    mock_contribution_objects.order_by.assert_called_once_with("-id")
                    mock_order_by.__getitem__.assert_called_once_with(
                        slice(None, 10)
                    )  # CONTRIBUTIONS_TAIL_SIZE * 2 = 5 * 2 = 10
                    mock_response.assert_called_once_with(mock_queryset)
                    assert isinstance(response, Response)


class TestApiViewsContributionsTailView:
    """Testing class for :py:class:`api.views.ContributionsTailView`."""

    @pytest.mark.asyncio
    async def test_api_views_contributions_tail_view_get(self, mocker):
        view = ContributionsTailView()
        mock_request = mocker.MagicMock()

        mock_queryset = mocker.MagicMock()

        # Mock sync_to_async to return awaitable
        with patch("api.views.sync_to_async") as mock_sync_to_async:
            mock_db_call = AsyncMock(return_value=mock_queryset)
            mock_sync_to_async.return_value = mock_db_call

            with patch("api.views.Contribution.objects") as mock_contribution_objects:
                # Mock the chain: objects.order_by().__getitem__()
                mock_order_by = mocker.MagicMock()
                mock_order_by.__getitem__.return_value = mock_queryset
                mock_contribution_objects.order_by.return_value = mock_order_by

                with patch(
                    "api.views.contributions_response", new_callable=AsyncMock
                ) as mock_response:
                    mock_response.return_value = Response([{"id": 1}])

                    response = await view.get(mock_request)

                    mock_contribution_objects.order_by.assert_called_once_with("-id")
                    mock_order_by.__getitem__.assert_called_once_with(
                        slice(None, 5)
                    )  # CONTRIBUTIONS_TAIL_SIZE = 5
                    mock_response.assert_called_once_with(mock_queryset)
                    assert isinstance(response, Response)


class TestApiViewsAddContributionView:
    """Testing class for :py:class:`api.views.AddContributionView`."""

    @pytest.mark.asyncio
    async def test_api_views_add_contribution_view_post_success(self, mocker):
        view = AddContributionView()
        mock_request = mocker.MagicMock()
        mock_request.data = {
            "username": "testuser",
            "platform": "twitter",
            "type": "[content] Content Creation",
            "level": "2",
            "url": "https://example.com",
            "comment": "Test contribution",
        }

        # Mock the sync_to_async wrapper to return an awaitable that returns the expected result
        mock_process = AsyncMock(return_value=({"id": 1}, None))

        with patch("api.views.sync_to_async", return_value=mock_process):
            response = await view.post(mock_request)

            mock_process.assert_called_once_with(mock_request.data)
            assert isinstance(response, Response)
            assert response.status_code == status.HTTP_201_CREATED
            assert response.data == {"id": 1}

    @pytest.mark.asyncio
    async def test_api_views_add_contribution_view_post_validation_error(self, mocker):
        view = AddContributionView()
        mock_request = mocker.MagicMock()
        mock_request.data = {
            "username": "testuser",
            "platform": "twitter",
            "type": "[content] Content Creation",
            "level": "2",
            "url": "invalid-url",  # This might cause validation error
            "comment": "Test contribution",
        }

        mock_errors = {"url": ["Enter a valid URL."]}
        mock_process = AsyncMock(return_value=(None, mock_errors))

        with patch("api.views.sync_to_async", return_value=mock_process):
            response = await view.post(mock_request)

            mock_process.assert_called_once_with(mock_request.data)
            assert isinstance(response, Response)
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert response.data == mock_errors

    @pytest.mark.asyncio
    async def test_api_views_add_contribution_view_post_inner_function_mocked(
        self, mocker
    ):
        # Test the full flow with mocked inner function
        view = AddContributionView()
        mock_request = mocker.MagicMock()
        mock_request.data = {
            "username": "testuser",
            "platform": "twitter",
            "type": "[content] Content Creation",
            "level": "2",
            "url": "https://example.com",
            "comment": "Test contribution",
        }

        # Mock the entire sync_to_async call chain
        with patch("api.views.sync_to_async") as mock_sync_to_async:
            # Create an awaitable mock that returns success
            mock_inner_function = AsyncMock(
                return_value=({"id": 1, "contributor": 1}, None)
            )
            mock_sync_to_async.return_value = mock_inner_function

            response = await view.post(mock_request)

            mock_sync_to_async.assert_called_once()
            mock_inner_function.assert_called_once_with(mock_request.data)
            assert response.status_code == status.HTTP_201_CREATED
