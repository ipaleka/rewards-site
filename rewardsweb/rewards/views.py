"""Module containing the views for the rewards app."""

from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from core.models import Contribution


class ClaimView(LoginRequiredMixin, TemplateView):
    """View for users to claim their rewards.

    This view displays the claim rewards interface, which allows authenticated
    users to initiate the process of claiming their earned rewards.
    """

    template_name = "rewards/claim.html"

    def get_context_data(self, **kwargs):
        """Add claimable status to the context.

        This method determines if the current user has a claimable allocation
        and adds a boolean `claimable` to the context.

        :param kwargs: Additional keyword arguments
        :return: Context dictionary with claimable status
        :rtype: dict
        """
        context = super().get_context_data(**kwargs)

        # TODO: Replace this with actual logic to check the Algorand box
        # based on the user's linked contributor address.
        contributor = getattr(self.request.user.profile, "contributor", None)
        if contributor and contributor.address:
            # Placeholder logic
            context["claimable"] = True
        else:
            context["claimable"] = False

        return context


@method_decorator(user_passes_test(lambda user: user.is_superuser), name="dispatch")
class AddAllocationsView(LoginRequiredMixin, TemplateView):
    """View for superusers to add new allocations.

    This view provides an interface for users with superuser privileges to add
    new reward allocations to the smart contract. It is restricted to
    superusers to prevent unauthorized modifications.
    """

    template_name = "rewards/add_allocations.html"

    def get_context_data(self, **kwargs):
        """Add any necessary context for the add allocations page.

        :param kwargs: Additional keyword arguments
        :return: Context dictionary
        :rtype: dict
        """
        context = super().get_context_data(**kwargs)
        addresses, amounts = Contribution.objects.addressed_contributions()
        context["allocations"] = zip(addresses, amounts)
        return context


@method_decorator(user_passes_test(lambda user: user.is_superuser), name="dispatch")
class ReclaimAllocationsView(LoginRequiredMixin, TemplateView):
    """View for superusers to reclaim allocations.

    This view allows superusers to reclaim reward allocations from the smart
    contract. This is typically done for allocations that are no longer valid
    or need to be returned. Access is restricted to superusers.
    """

    template_name = "rewards/reclaim_allocations.html"

    def get_context_data(self, **kwargs):
        """Add any necessary context for the reclaim allocations page.

        :param kwargs: Additional keyword arguments
        :return: Context dictionary
        :rtype: dict
        """
        context = super().get_context_data(**kwargs)
        # TODO: Add any context needed for the template, if any.
        return context
