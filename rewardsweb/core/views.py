"""Module containing website's views."""

from django.db.models import Sum
from django.views.generic import DetailView, ListView
from django.views.generic.base import TemplateView

from core.models import Contribution, Contributor, Cycle


class IndexView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, *args, **kwargs):
        """Update context with the database records count.

        :return: dict
        """
        context = super().get_context_data(*args, **kwargs)

        num_cycles = Cycle.objects.all().count()
        num_contributors = Contributor.objects.all().count()
        num_contributions = Contribution.objects.all().count()
        total_rewards = Contribution.objects.aggregate(
            total_rewards=Sum("reward__amount")
        ).get("total_rewards", 0)

        context["num_cycles"] = num_cycles
        context["num_contributors"] = num_contributors
        context["num_contributions"] = num_contributions
        context["total_rewards"] = total_rewards

        return context


class ContributionDetailView(DetailView):
    model = Contribution


class ContributorListView(ListView):
    model = Contributor
    paginate_by = 20


class ContributorDetailView(DetailView):
    model = Contributor


class CycleListView(ListView):
    model = Cycle
    paginate_by = 20

    def get_queryset(self):
        return Cycle.objects.all().reverse()


class CycleDetailView(DetailView):
    model = Cycle
