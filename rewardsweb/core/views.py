"""Module containing website's views."""

import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Q, Sum
from django.forms import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, FormView, ListView, UpdateView
from django.views.generic.detail import SingleObjectMixin

from core.forms import (
    ContributionEditForm,
    CreateIssueForm,
    IssueLabelsForm,
    ProfileFormSet,
    UpdateUserForm,
)
from core.models import Contribution, Contributor, Cycle, Issue, IssueStatus
from utils.bot import add_reaction_to_message
from utils.constants.core import (
    DISCORD_NOTED_EMOJI,
    ISSUE_CREATION_LABEL_CHOICES,
    ISSUE_PRIORITY_CHOICES,
)
from utils.issues import (
    close_issue_with_labels,
    create_github_issue,
    issue_by_number,
    issue_data_for_contribution,
    set_labels_to_issue,
)

logger = logging.getLogger(__name__)


class IndexView(ListView):
    """View for displaying the main index page with contribution statistics.

    Displays a paginated list of unconfirmed contributions along with
    overall platform statistics.

    :ivar model: Model class for contributions
    :type model: :class:`core.models.Contribution`
    :ivar paginate_by: Number of items per page
    :type paginate_by: int
    :ivar template_name: HTML template for the index page
    :type template_name: str
    """

    model = Contribution
    paginate_by = 20
    template_name = "index.html"

    def get_context_data(self, *args, **kwargs):
        """Update context with the database records count.

        :param args: Additional positional arguments
        :param kwargs: Additional keyword arguments
        :return: Context dictionary with statistics data
        :rtype: dict
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

    def get_queryset(self):
        """Return queryset of unconfirmed contributions in reverse order.

        :return: QuerySet of unconfirmed contributions
        :rtype: :class:`django.db.models.QuerySet`
        """
        return Contribution.objects.filter(confirmed=False).reverse()


class ContributionDetailView(DetailView):
    """View for displaying detailed information about a single contribution.

    :ivar model: Model class for contributions
    :type model: :class:`core.models.Contribution`
    """

    model = Contribution


@method_decorator(user_passes_test(lambda user: user.is_superuser), name="dispatch")
class ContributionUpdateView(UpdateView):
    """View for updating contribution information (superusers only).

    Allows superusers to edit contribution details including reward,
    percentage, and comments.

    :ivar model: Model class for contributions
    :type model: :class:`core.models.Contribution`
    :ivar form_class: Form class for editing contributions
    :type form_class: :class:`core.forms.ContributionEditForm`
    :ivar template_name: HTML template for the edit form
    :type template_name: str
    """

    model = Contribution
    form_class = ContributionEditForm
    template_name = "core/contribution_edit.html"

    def get_success_url(self):
        """Return URL to redirect after successful update.

        :return: URL for contribution detail page with success message
        :rtype: str
        """
        messages.success(self.request, "Contribution updated successfully!")
        return reverse_lazy("contribution-detail", kwargs={"pk": self.object.pk})


class ContributorListView(ListView):
    """View for displaying a paginated list of all contributors.

    :ivar model: Model class for contributors
    :type model: :class:`core.models.Contributor`
    :ivar paginate_by: Number of items per page
    :type paginate_by: int
    """

    model = Contributor
    paginate_by = 20

    def get_queryset(self):
        """Return filtered queryset based on search query.

        :return: QuerySet of contributors filtered by search term
        :rtype: :class:`django.db.models.QuerySet`
        """
        queryset = super().get_queryset()

        # Get search query from GET parameters
        search_query = self.request.GET.get("q")
        if search_query:
            # Search in contributor names and handle handles
            queryset = queryset.filter(
                Q(name__icontains=search_query)
                | Q(handle__handle__icontains=search_query)
            ).distinct()

        return queryset

    def get_context_data(self, **kwargs):
        """Add search query to template context.

        :param kwargs: Additional keyword arguments
        :return: Context dictionary with search data
        :rtype: dict
        """
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        return context


class ContributorDetailView(DetailView):
    """View for displaying detailed information about a single contributor.

    :ivar model: Model class for contributors
    :type model: :class:`core.models.Contributor`
    """

    model = Contributor


class CycleListView(ListView):
    """View for displaying a paginated list of all cycles in reverse order.

    :ivar model: Model class for cycles
    :type model: :class:`core.models.Cycle`
    :ivar paginate_by: Number of items per page
    :type paginate_by: int
    """

    model = Cycle
    paginate_by = 10

    def get_queryset(self):
        """Return queryset of all cycles in reverse chronological order.

        :return: QuerySet of cycles in reverse order
        :rtype: :class:`django.db.models.QuerySet`
        """
        return Cycle.objects.all().reverse()


class CycleDetailView(DetailView):
    """View for displaying detailed information about a single cycle.

    :ivar model: Model class for cycles
    :type model: :class:`core.models.Cycle`
    """

    model = Cycle


# core/views.py
class IssueDetailView(DetailView):
    """View for displaying detailed information about a single issue."""

    model = Issue

    def get_context_data(self, **kwargs):
        """Add GitHub issue data and form to template context."""
        context = super().get_context_data(**kwargs)

        issue = self.get_object()
        context["issue_html_url"] = (
            f"https://github.com/{settings.GITHUB_REPO_OWNER}/"
            f"{settings.GITHUB_REPO_NAME}/issues/{issue.number}"
        )

        # Only fetch GitHub data and show form for superusers
        if self.request.user.is_superuser:
            # Retrieve GitHub issue data if issue number exists
            issue_data = issue_by_number(self.request.user, issue.number)

            if issue_data["success"]:
                context["github_issue"] = issue_data["issue"]
                context["issue_title"] = issue_data["issue"]["title"]
                context["issue_body"] = issue_data["issue"]["body"]
                context["issue_state"] = issue_data["issue"]["state"]
                context["issue_labels"] = issue_data["issue"]["labels"]
                context["issue_assignees"] = issue_data["issue"]["assignees"]
                context["issue_html_url"] = issue_data["issue"]["html_url"]
                context["issue_created_at"] = issue_data["issue"]["created_at"]
                context["issue_updated_at"] = issue_data["issue"]["updated_at"]

                # Only show forms if GitHub issue is open
                if issue_data["issue"]["state"] == "open":
                    # Extract current labels and priority from GitHub issue
                    current_labels = issue_data["issue"]["labels"]
                    selected_labels = []
                    selected_priority = "medium priority"  # Default

                    # Get available labels and priorities for matching
                    available_labels = [
                        choice[0] for choice in ISSUE_CREATION_LABEL_CHOICES
                    ]
                    available_priorities = [
                        choice[0] for choice in ISSUE_PRIORITY_CHOICES
                    ]

                    # Separate labels from priority
                    for label in current_labels:
                        # Check if this is a priority label (exact match with available priorities)
                        if label in available_priorities:
                            selected_priority = label
                        # Check if this is a regular label (exact match with available labels)
                        elif label in available_labels:
                            selected_labels.append(label)

                    # Create form with initial values
                    initial_data = {
                        "labels": selected_labels,
                        "priority": selected_priority,
                    }
                    context["labels_form"] = IssueLabelsForm(initial=initial_data)

                    # Add context variables for template
                    context["current_priority"] = selected_priority
                    context["current_custom_labels"] = selected_labels

            else:
                context["github_error"] = issue_data["error"]

        return context

    def post(self, request, *args, **kwargs):
        """Handle form submission for both labels and close actions."""
        # Only superusers can submit forms
        if not request.user.is_superuser:
            messages.error(request, "You don't have permission to perform this action.")
            return redirect("issue-detail", pk=self.get_object().pk)

        issue = self.get_object()

        # Check which form was submitted
        if "submit_labels" in request.POST:
            # Handle labels form submission
            return self._handle_labels_submission(request, issue)
        elif "submit_close" in request.POST:
            # Handle close issue submission
            return self._handle_close_submission(request, issue)
        else:
            messages.error(request, "Invalid form submission.")
            return redirect("issue-detail", pk=issue.pk)

    def _handle_labels_submission(self, request, issue):
        """Handle the labels form submission."""
        form = IssueLabelsForm(request.POST)

        if form.is_valid():
            # Combine selected labels with priority
            labels_to_add = form.cleaned_data["labels"] + [
                form.cleaned_data["priority"]
            ]

            # Call the function to set labels to GitHub issue
            result = set_labels_to_issue(request.user, issue.number, labels_to_add)

            if result["success"]:
                messages.success(
                    request,
                    f"Successfully set labels for issue #{issue.number}: {', '.join(labels_to_add)}",
                )
            else:
                messages.error(
                    request,
                    f"Failed to set labels: {result.get('error', 'Unknown error')}",
                )
        else:
            messages.error(request, "Please correct the errors in the form.")

        return redirect("issue-detail", pk=issue.pk)

    def _handle_close_submission(self, request, issue):
        """Handle the close issue submission."""
        action = request.POST.get("close_action")
        comment = request.POST.get("close_comment", "")

        if action not in ["resolved", "wontfix"]:
            messages.error(request, "Invalid close action.")
            return redirect("issue-detail", pk=issue.pk)

        try:
            # Get current labels from GitHub
            issue_data = issue_by_number(request.user, issue.number)
            if not issue_data["success"]:
                messages.error(
                    request, f"Failed to fetch GitHub issue: {issue_data.get('error')}"
                )
                return redirect("issue-detail", pk=issue.pk)

            # Check if issue is still open
            if issue_data["issue"]["state"] != "open":
                messages.error(
                    request, "Cannot close an issue that is already closed on GitHub."
                )
                return redirect("issue-detail", pk=issue.pk)

            current_labels = issue_data["issue"]["labels"]

            # Remove "work in progress" and prepare labels
            labels_to_set = [
                label for label in current_labels if label.lower() != "work in progress"
            ]

            if action == "resolved":
                # Add "addressed" label
                if "addressed" not in labels_to_set:
                    labels_to_set.append("addressed")
                # Update local issue status
                issue.status = IssueStatus.ADDRESSED
                success_message = (
                    f"Issue #{issue.number} closed as resolved successfully."
                )

            else:
                # Add "wontfix" label
                if "wontfix" not in labels_to_set:
                    labels_to_set.append("wontfix")
                # Update local issue status
                issue.status = IssueStatus.WONTFIX
                success_message = (
                    f"Issue #{issue.number} closed as wontfix successfully."
                )

            # Save local issue status
            issue.save()

            # Call the function to close issue on GitHub
            result = close_issue_with_labels(
                user=request.user,
                issue_number=issue.number,
                labels_to_set=labels_to_set,
                comment=comment,
            )

            if result["success"]:
                messages.success(request, success_message)
            else:
                # Revert local status if GitHub operation failed
                issue.status = IssueStatus.CREATED
                issue.save()
                messages.error(
                    request, result.get("error", "Failed to close issue on GitHub")
                )

        except Exception as e:
            messages.error(request, f"Error closing issue: {str(e)}")

        return redirect("issue-detail", pk=issue.pk)


@method_decorator(user_passes_test(lambda user: user.is_superuser), name="dispatch")
class CreateIssueView(FormView):
    """View for creating GitHub issues from contributions.

    This view allows superusers to create GitHub issues based on contribution data.
    It pre-populates the form with data from the contribution and handles the
    GitHub API integration for issue creation.

    :ivar template_name: HTML template for the create issue form
    :type template_name: str
    :ivar form_class: Form class for creating GitHub issues
    :type form_class: :class:`core.forms.CreateIssueForm`
    :ivar contribution_id: ID of the contribution being processed
    :type contribution_id: int
    """

    template_name = "create_issue.html"
    form_class = CreateIssueForm

    def get(self, request, *args, **kwargs):
        """Handle GET request for the create issue form.

        :param request: HTTP request object
        :type request: :class:`django.http.HttpRequest`
        :param args: Additional positional arguments
        :param kwargs: Additional keyword arguments including contribution_id
        :return: :class:`django.http.HttpResponse`
        """
        # Store the initial ID from URL when the form is first loaded
        self.contribution_id = kwargs.get("contribution_id")
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Handle POST request for form submission.

        :param request: HTTP request object
        :type request: :class:`django.http.HttpRequest`
        :param args: Additional positional arguments
        :param kwargs: Additional keyword arguments including contribution_id
        :return: :class:`django.http.HttpResponse`
        """
        # Store the initial ID from URL when form is submitted
        self.contribution_id = kwargs.get("contribution_id")
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        """Return URL to redirect after successful form submission.

        :return: str
        """
        return reverse_lazy("contribution-detail", args=[self.contribution_id])

    def get_initial(self):
        """Set initial form data from contribution.

        :return: dict
        """
        initial = super().get_initial()

        if self.contribution_id:
            data = issue_data_for_contribution(
                Contribution.objects.get(id=self.contribution_id)
            )
        else:
            data = {
                "priority": "medium priority",
                "issue_body": "Please provide issue description here.",
                "issue_title": "Issue title",
            }

        initial.update(data)
        return initial

    def get_context_data(self, **kwargs):
        """Add contribution context data to template.

        :param kwargs: Additional keyword arguments
        :return: dict
        """
        context = super().get_context_data(**kwargs)

        info = Contribution.objects.get(id=self.contribution_id).info()
        context["contribution_id"] = self.contribution_id
        context["contribution_info"] = info
        context["page_title"] = f"Create issue for {info}"

        return context

    def form_valid(self, form):
        """Process valid form data and create GitHub issue.

        :param form: Validated form instance
        :type form: :class:`core.forms.CreateIssueForm`
        :return: :class:`django.http.HttpResponseRedirect`
        """
        cleaned_data = form.cleaned_data

        labels = cleaned_data.get("labels", [])
        priority = cleaned_data.get("priority", "")
        issue_body = cleaned_data.get("issue_body", "")
        issue_title = cleaned_data.get("issue_title", "")
        data = create_github_issue(
            self.request.user, issue_title, issue_body, labels=labels + [priority]
        )
        if not data.get("success"):
            form.add_error(
                None, ValidationError(data.get("error"))
            )  # None adds to non-field errors
            return self.form_invalid(form)

        contribution = Contribution.objects.get(id=self.contribution_id)
        Issue.objects.confirm_contribution_with_issue(
            data.get("issue_number"), contribution
        )

        add_reaction_to_message(contribution.url, DISCORD_NOTED_EMOJI)

        return super().form_valid(form)


# # USER/PROFILE
class ProfileDisplay(DetailView):
    """Displays user's profile page

    Django generic CBV DetailView needs template and model to be declared.

    :class:`ProfileEditView` is the main class for viewing and updating
    user/prodfile data and it uses this class as GET part of the process.
    """

    template_name = "profile.html"
    model = User

    def get(self, request, *args, **kwargs):
        """Handles GET requests and instantiates blank versions of the form

        and its inline formset. User editing form is get by class' get_form
        method and profile editing formset is instantiated here.
        """
        self.object = None
        form = self.get_form()
        profile_form = ProfileFormSet(instance=self.request.user)
        return self.render_to_response(
            self.get_context_data(form=form, profile_form=profile_form)
        )

    def get_form(self, form_class=None):
        """Instantiates and returns form for updating profile data

        :class:`UpdateUserForm` is used to instantiate form with instance set
        to user object and form's data from the same object

        :return: instance of profile editing form
        """
        self.object = self.request.user
        data = {
            "first_name": self.object.first_name,
            "last_name": self.object.last_name,
            "email": self.object.email,
        }
        return UpdateUserForm(instance=self.object, data=data)


class ProfileUpdate(UpdateView, SingleObjectMixin):
    """Updates user/profile`data

    Django generic CBV UpdateView and SingleObjectMixin needs template,
    model and form_class to be declared, :class:`ProfileEditView` is the main
    class in updating profile data process and it uses this class as the
    POST part of the process.
    """

    template_name = "profile.html"
    model = User
    form_class = UpdateUserForm
    success_url = reverse_lazy("profile")

    def get_object(self, queryset=None):
        """Returns/sets user object

        Overriding this method is Django DetailView requirement

        :return: user instance
        """
        return self.request.user

    def get_form(self, *args, **kwargs):
        """Instantiates and returns form for editing user/profile data

        Instance's user object is the request user's instance and it's used
        by form_class to instantiate form.

        :return: instance of user/profile editing form
        """
        self.object = self.request.user
        return self.form_class(instance=self.object, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating a form instance and its inline
        formset with the passed POST variables and then checking them for
        validity.
        """
        self.object = None
        form = self.get_form(request.POST)
        profile_form = ProfileFormSet(instance=self.request.user, data=request.POST)
        if form.is_valid() and profile_form.is_valid():
            return self.form_valid(form, profile_form)
        return self.form_invalid(form, profile_form)

    def form_valid(self, form, profile_form):
        """
        Called if all forms are valid. Updates a User instance along with
        associated Profile and then redirects to a success page.
        """
        self.object = form.save()
        profile_form.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, profile_form):
        """
        Called if a form is invalid. Re-renders the context data with the
        data-filled forms and errors.
        """
        return self.render_to_response(
            self.get_context_data(form=form, profile_form=profile_form)
        )


@method_decorator(login_required(login_url="/accounts/login/"), name="dispatch")
class ProfileEditView(View):
    """Update and displays profile data"""

    def get(self, request, *args, **kwargs):
        """Sets :class:`ProfileDisplay` get method as its own GET

        :return: :class:`ProfileDisplay` as_view method
        """
        view = ProfileDisplay.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Sets :class:`ProfileUpdate` post method as its own POST

        :return: :class:`ProfileUpdate` as_view method
        """
        view = ProfileUpdate.as_view()
        return view(request, *args, **kwargs)
