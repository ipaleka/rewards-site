"""Module containing the views for the rewards app."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


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
