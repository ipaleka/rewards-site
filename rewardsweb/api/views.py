from adrf.views import APIView
from rest_framework.response import Response
from rest_framework import status
from asgiref.sync import sync_to_async
from django.db import transaction

from core.models import Contribution, Contributor, Cycle
from api.serializers import (
    AggregatedCycleSerializer,
    ContributionSerializer,
    CycleSerializer,
    HumanizedContributionSerializer,
)


class ContributionsView(APIView):
    async def get(self, request):
        username = request.GET.get("name")

        if username:
            contributor = await sync_to_async(
                lambda: Contributor.objects.from_handle(username)
            )()
            contributions = await sync_to_async(
                lambda: list(Contribution.objects.filter(contributor=contributor))
            )()

        else:
            contributions = await sync_to_async(
                lambda: list(Contribution.objects.all().order_by("-id")[:10])
            )()

        serializer = ContributionSerializer(contributions, many=True)
        return Response(serializer.data)


class AddContributionView(APIView):
    async def post(self, request):
        serializer = ContributionSerializer(data=request.data)

        if await sync_to_async(serializer.is_valid)():
            # Use atomic transaction for safety
            async with transaction.atomic():
                await sync_to_async(serializer.save)()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CurrentCycleAggregatedView(APIView):
    async def get(self, request):
        # Async database query
        cycle = await sync_to_async(lambda: Cycle.objects.latest("start"))()
        contributor_rewards = await sync_to_async(lambda: cycle.contributor_rewards)()
        total_rewards = await sync_to_async(lambda: cycle.total_rewards)()
        data = {
            "id": cycle.id,
            "start": cycle.start,
            "end": cycle.end,
            "contributor_rewards": contributor_rewards,
            "total_rewards": total_rewards,
        }
        serializer = AggregatedCycleSerializer(data=data)
        serializer.is_valid()
        return Response(serializer.data)


class CurrentCyclePlainView(APIView):
    async def get(self, request):
        # Async database query
        cycle = await sync_to_async(lambda: Cycle.objects.latest("start"))()

        serializer = CycleSerializer(cycle)
        return Response(serializer.data)


class CycleAggregatedView(APIView):
    async def get(self, request, cycle_id):
        # Async database query
        cycle = await sync_to_async(lambda: Cycle.objects.filter(id=cycle_id).first())()

        if not cycle:
            return Response(
                {"error": "Cycle not found"}, status=status.HTTP_404_NOT_FOUND
            )

        contributor_rewards = await sync_to_async(lambda: cycle.contributor_rewards)()
        total_rewards = await sync_to_async(lambda: cycle.total_rewards)()
        data = {
            "id": cycle.id,
            "start": cycle.start,
            "end": cycle.end,
            "contributor_rewards": contributor_rewards,
            "total_rewards": total_rewards,
        }
        serializer = AggregatedCycleSerializer(data=data)
        serializer.is_valid()
        return Response(serializer.data)


class ContributionsTailView(APIView):
    async def get(self, request):
        data = await sync_to_async(
            lambda: [
                {
                    "id": contribution.id,
                    "contributor_name": contribution.contributor.name,
                    "cycle_id": contribution.cycle.id,
                    "platform": contribution.platform.name,
                    "url": contribution.url,
                    "type": contribution.reward.type,
                    "level": contribution.reward.level,
                    "percentage": contribution.percentage,
                    "reward": contribution.reward.amount,
                    "confirmed": contribution.confirmed,
                }
                for contribution in Contribution.objects.order_by("-id")[:5]
            ]
        )()
        serializer = HumanizedContributionSerializer(data=data, many=True)
        serializer.is_valid()
        return Response(serializer.data)
