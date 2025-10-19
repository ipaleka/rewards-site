"""Module containing ASA Stats Rewards API views."""

from adrf.views import APIView
from asgiref.sync import sync_to_async
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status

from core.models import (
    Contribution,
    Contributor,
    Cycle,
    Reward,
    RewardType,
    SocialPlatform,
)
from api.serializers import (
    AggregatedCycleSerializer,
    ContributionSerializer,
    CycleSerializer,
    HumanizedContributionSerializer,
)
from utils.constants.core import CONTRIBUTIONS_TAIL_SIZE
from utils.helpers import humanize_contributions


# # HELPERS
async def aggregated_cycle_response(cycle: Cycle):
    if not cycle:
        return Response({"error": "Cycle not found"}, status=status.HTTP_404_NOT_FOUND)

    contributor_rewards = await sync_to_async(lambda: cycle.contributor_rewards)()
    total_rewards = await sync_to_async(lambda: cycle.total_rewards)()

    data = {
        "id": cycle.id,
        "start": cycle.start,
        "end": cycle.end,
        "contributor_rewards": contributor_rewards,
        "total_rewards": total_rewards or 0,
    }

    serializer = AggregatedCycleSerializer(data=data)
    serializer.is_valid()
    return Response(serializer.data)


async def contributions_response(contributions):
    """Fetch, humanize, serialize, and return contributions."""

    # Run DB-dependent humanization on a thread pool
    data = await sync_to_async(lambda: humanize_contributions(contributions))()
    serializer = HumanizedContributionSerializer(data=data, many=True)
    serializer.is_valid()
    return Response(serializer.data)


class CycleAggregatedView(APIView):
    async def get(self, request, cycle_id):
        cycle = await sync_to_async(lambda: Cycle.objects.filter(id=cycle_id).first())()
        return await aggregated_cycle_response(cycle)


class CurrentCycleAggregatedView(APIView):
    async def get(self, request):
        cycle = await sync_to_async(lambda: Cycle.objects.latest("start"))()
        return await aggregated_cycle_response(cycle)


class CyclePlainView(APIView):
    async def get(self, request, cycle_id):
        cycle = await sync_to_async(lambda: Cycle.objects.filter(id=cycle_id).first())()
        if not cycle:
            return Response(
                {"error": "Cycle not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = CycleSerializer(cycle)
        return Response(serializer.data)


class CurrentCyclePlainView(APIView):
    async def get(self, request):
        # Async database query
        cycle = await sync_to_async(lambda: Cycle.objects.latest("start"))()
        serializer = CycleSerializer(cycle)
        return Response(serializer.data)


class ContributionsView(APIView):
    async def get(self, request):
        username = request.GET.get("name")

        if username:
            contributor = await sync_to_async(
                lambda: Contributor.objects.from_handle(username)
            )()
            queryset = Contribution.objects.filter(contributor=contributor)
        else:
            queryset = Contribution.objects.order_by("-id")[
                : CONTRIBUTIONS_TAIL_SIZE * 2
            ]

        return await contributions_response(queryset)


class ContributionsTailView(APIView):
    async def get(self, request):
        queryset = Contribution.objects.order_by("-id")[:CONTRIBUTIONS_TAIL_SIZE]
        return await contributions_response(queryset)


class AddContributionView(APIView):
    async def post(self, request):

        @sync_to_async
        def process_contribution(raw_data):
            contributor = Contributor.objects.from_handle(raw_data.get("username"))
            cycle = Cycle.objects.latest("start")
            platform = SocialPlatform.objects.get(name=raw_data.get("platform"))
            label, name = (
                raw_data.get("type").split(" ", 1)[0].strip("[]"),
                raw_data.get("type").split(" ", 1)[1].strip(),
            )
            reward_type = get_object_or_404(RewardType, label=label, name=name)
            rewards = Reward.objects.filter(
                type=reward_type, level=int(raw_data.get("level", 1)), active=True
            )
            data = {
                "contributor": contributor.id,
                "cycle": cycle.id,
                "platform": platform.id,
                "reward": rewards[0].id,
                "percentage": 1,
                "url": raw_data.get("url"),
                "comment": raw_data.get("comment"),
                "confirmed": False,
            }

            serializer = ContributionSerializer(data=data)
            if serializer.is_valid():
                with transaction.atomic():
                    serializer.save()

                return serializer.data, None

            return None, serializer.errors

        data, errors = await process_contribution(request.data)
        if data:
            return Response(data, status=status.HTTP_201_CREATED)

        return Response(errors, status=status.HTTP_400_BAD_REQUEST)
