from adrf.views import APIView
from rest_framework.response import Response
from rest_framework import status
from asgiref.sync import sync_to_async
from django.db import transaction

from core.models import Contribution, Contributor, Cycle
from api.serializers import ContributionSerializer, CycleSerializer


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


class CycleAggregatedView(APIView):
    async def get(self, request):
        # Async database query
        cycle_data = await sync_to_async(lambda: Cycle.objects.latest("start"))()

        serializer = CycleSerializer(cycle_data)
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


class CycleDatesView(APIView):
    async def get(self, request, cycle_id):
        cycle_dates = await sync_to_async(
            lambda: Cycle.objects.filter(id=cycle_id).values("start", "end").first()
        )()

        if not cycle_dates:
            return Response(
                {"error": "Cycle not found"}, status=status.HTTP_404_NOT_FOUND
            )

        return Response(cycle_dates)


class ContributionsLastView(APIView):
    async def get(self, request):
        last_contributions = await sync_to_async(
            lambda: list(Contribution.objects.order_by("-id")[:5])
        )()

        serializer = ContributionSerializer(last_contributions, many=True)
        return Response(serializer.data)
