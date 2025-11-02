"""Module containing website's views."""

import logging
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Prefetch, Q, Sum
from django.db.models.functions import Lower
from django.forms import ValidationError
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, FormView, ListView, UpdateView
from django.views.generic.detail import SingleObjectMixin

from core.forms import (
    ContributionEditForm,
    ContributionInvalidateForm,
    CreateIssueForm,
    IssueLabelsForm,
    ProfileFormSet,
    UpdateUserForm,
)
from core.models import Contribution, Contributor, Cycle, Handle, Issue, IssueStatus
from utils.bot import add_reaction_to_message, add_reply_to_message, message_from_url
from utils.constants.core import (
    DISCORD_EMOJIS,
    ISSUE_CREATION_LABEL_CHOICES,
    ISSUE_PRIORITY_CHOICES,
)
from utils.constants.ui import MISSING_TOKEN_TEXT
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
class ContributionEditView(UpdateView):
    """View for updating contribution information (superusers only).

    Allows superusers to edit contribution details including reward,
    percentage, comments, GitHub issue number, and issue status.

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

    def form_valid(self, form):
        """Handle form validation with GitHub issue processing."""
        issue_number = form.cleaned_data.get("issue_number")
        issue_status = form.cleaned_data.get("issue_status", IssueStatus.CREATED)

        if issue_number:
            # Check if issue with this number already exists
            try:
                issue = Issue.objects.get(number=issue_number)
                # Update existing issue status if provided
                if issue_status and issue.status != issue_status:
                    issue.status = issue_status
                    issue.save()
                    self.request.user.profile.log_action("issue_status_set", str(issue))
                form.instance.issue = issue

            except Issue.DoesNotExist:
                # Check if GitHub issue exists
                issue_data = issue_by_number(self.request.user, issue_number)
                if not issue_data.get("success"):
                    if issue_data.get("error") == MISSING_TOKEN_TEXT:
                        form.add_error(
                            "issue_number", "That GitHub issue doesn't exist!"
                        )
                    else:
                        form.add_error("issue_number", MISSING_TOKEN_TEXT)
                    return self.form_invalid(form)

                # Create new issue with selected status
                issue = Issue.objects.create(
                    number=issue_number, status=issue_status or IssueStatus.CREATED
                )
                self.request.user.profile.log_action("issue_created", str(issue))
                form.instance.issue = issue
        else:
            # If issue_number is empty or None, remove the issue association
            form.instance.issue = None

        return super().form_valid(form)

    def get_success_url(self):
        """Return URL to redirect after successful update.

        :return: URL for contribution detail page with success message
        :rtype: str
        """
        self.request.user.profile.log_action(
            "contribution_edited", Contribution.objects.get(id=self.object.pk).info()
        )
        messages.success(self.request, "Contribution updated successfully!")
        return reverse_lazy("contribution-detail", kwargs={"pk": self.object.pk})


@method_decorator(user_passes_test(lambda user: user.is_superuser), name="dispatch")
class ContributionInvalidateView(UpdateView):
    """View for setting contribution as duplicate or wontfix."""

    model = Contribution
    form_class = ContributionInvalidateForm
    template_name = "core/contribution_invalidate.html"

    def get_context_data(self, *args, **kwargs):
        """Add original Discord message text to template context."""
        context = super().get_context_data(*args, **kwargs)

        context["type"] = self.kwargs.get("reaction")

        contribution = self.object  # Use self.object instead of querying again
        message = message_from_url(contribution.url)
        if message.get("success"):
            author = message.get("author")
            timestamp = datetime.strptime(
                message.get("timestamp"), "%Y-%m-%dT%H:%M:%S.%f%z"
            ).strftime("%d %b %H:%M")
            original_comment = f"    {author} - {timestamp}\n\n"
            for line in message.get("content").split("\n"):
                original_comment += f"{line}\n"

            context["original_comment"] = original_comment

        else:
            context["original_comment"] = ""  # Set empty string when no message

        return context

    def form_valid(self, form):
        """Set contribution as confirmed with reaction and optional reply."""
        reaction = self.kwargs.get("reaction")
        comment = form.cleaned_data.get("comment")

        # Track operations that need to be performed
        operations = []
        if comment:
            operations.append("reply")
        operations.append("reaction")

        # Perform operations and track failures
        failed_operations = []

        # Add reply if comment exists
        reply_success = True
        if comment:
            try:
                reply_success = add_reply_to_message(self.object.url, comment)
                if not reply_success:
                    failed_operations.append("reply")
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to add reply: {str(e)}")
                failed_operations.append("reply")

        # Add reaction
        reaction_success = True
        try:

            reaction_success = add_reaction_to_message(
                self.object.url, DISCORD_EMOJIS.get(reaction)
            )
            if not reaction_success:
                failed_operations.append("reaction")

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to add reaction: {str(e)}")
            failed_operations.append("reaction")

        # If any operation failed, don't confirm and show error
        if failed_operations:
            error_msg = self._get_error_message(failed_operations, operations, reaction)
            form.add_error(None, error_msg)
            return self.form_invalid(form)

        # All operations successful - confirm the contribution
        self.object.confirmed = True
        self.object.save()
        self.request.user.profile.log_action(
            "contribution_invalidated", self.object.info()
        )

        # Success message
        success_msg = self._get_success_message(comment, reaction)
        messages.success(self.request, success_msg)

        return super().form_valid(form)

    def _get_error_message(self, failed_operations, attempted_operations, reaction):
        """Generate appropriate error message based on failed operations."""
        if len(failed_operations) == len(attempted_operations):
            return f"Failed to set contribution as {reaction}. All operations failed."

        failed_ops_str = " and ".join(failed_operations)
        return (
            f"Failed to add {failed_ops_str}. Contribution was not set as {reaction}."
        )

    def _get_success_message(self, comment, reaction):
        """Generate appropriate success message."""
        actions = [f"set as {reaction}"]
        if comment:
            actions.append("reply sent")
        actions.append("reaction added")

        actions_str = " and ".join(actions)
        return f"Contribution {actions_str} successfully!"

    def get_success_url(self):
        """Return URL to redirect after successful update."""
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
            return queryset.filter(
                Q(name__icontains=search_query)
                | Q(handle__handle__icontains=search_query)
            ).distinct()

        return queryset.prefetch_related(
            Prefetch(
                "handle_set",
                queryset=Handle.objects.order_by(Lower("handle")),
                to_attr="prefetched_handles",
            )
        )

    def get_context_data(self, *args, **kwargs):
        """Add search query to template context.

        :param kwargs: Additional keyword arguments
        :return: Context dictionary with search data
        :rtype: dict
        """
        context = super().get_context_data(*args, **kwargs)
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

    def get_queryset(self):
        """Optimize queryset to reduce database queries.

        :return: QuerySet of this cycle's contributions ordered by ID in reverse
        :rtype: :class:`django.db.models.QuerySet`
        """
        return (
            super()
            .get_queryset()
            .prefetch_related(
                Prefetch(
                    "contribution_set",
                    queryset=Contribution.objects.select_related(
                        "contributor", "reward__type", "platform"
                    ).order_by("-id"),
                )
            )
        )


class IssueListView(ListView):
    """View for displaying a paginated list of all open issues in reverse order.

    :ivar model: Model class for cycles
    :type model: :class:`core.models.Cycle`
    :ivar paginate_by: Number of items per page
    :type paginate_by: int
    """

    model = Issue
    paginate_by = 20

    def get_queryset(self):
        """Return open issues queryset in reverse order with prefetched contributions.

        :return: QuerySet of open issues in reverse order
        :rtype: :class:`django.db.models.QuerySet`
        """
        return Issue.objects.filter(status=IssueStatus.CREATED).prefetch_related(
            Prefetch(
                "contribution_set",
                queryset=Contribution.objects.select_related(
                    "contributor", "platform", "reward__type"
                ).order_by("created_at"),
                to_attr="prefetched_contributions",
            )
        )


class IssueDetailView(DetailView):
    """View for displaying detailed information about a single issue."""

    model = Issue

    def get_context_data(self, *args, **kwargs):
        """Add GitHub issue data and form to template context."""
        context = super().get_context_data(*args, **kwargs)

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
            labels_to_add = form.cleaned_data["labels"] + [
                form.cleaned_data["priority"]
            ]

            result = set_labels_to_issue(request.user, issue.number, labels_to_add)

            if result["success"]:
                success_message = (
                    f"Successfully set labels for issue #{issue.number}: "
                    f"{', '.join(labels_to_add)}"
                )
                messages.success(request, "Labels updated successfully")

                request.user.profile.log_action("issue_labels_set", success_message)

            else:
                messages.error(
                    request,
                    f"Failed to set labels: {result.get('error', 'Unknown error')}",
                )

        else:
            messages.error(request, "Please correct the errors in the form.")

        if request.headers.get("HX-Request") == "true":
            msg_obj = next(iter(messages.get_messages(request)), None)

            html = render_to_string(
                "core/issue_detail.html#labels_form_partial",
                {
                    "labels_form": form,
                    "issue": issue,
                    "toast_message": msg_obj.message if msg_obj else None,
                    "toast_type": msg_obj.tags if msg_obj else None,
                },
                request=request,
            )
            return HttpResponse(html)

        return redirect("issue-detail", pk=issue.pk)

    def _handle_close_submission(self, request, issue):
        """Handle the close issue submission."""
        action = request.POST.get("close_action")
        comment = request.POST.get("close_comment", "")

        if action not in ["addressed", "wontfix"]:
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

            if action not in labels_to_set:
                labels_to_set.append(action)

            success_message = f"Issue #{issue.number} closed as {action} successfully."

            # Call the function to close issue on GitHub
            result = close_issue_with_labels(
                user=request.user,
                issue_number=issue.number,
                labels_to_set=labels_to_set,
                comment=comment,
            )

            if result["success"]:
                self.request.user.profile.log_action("issue_closed", success_message)
                messages.success(request, success_message)
                for contribution in self.get_object().contribution_set.all():
                    add_reaction_to_message(
                        contribution.url, DISCORD_EMOJIS.get(action)
                    )

                issue.status = (
                    IssueStatus.ADDRESSED
                    if action == "addressed"
                    else IssueStatus.WONTFIX
                )
                issue.save()
                self.request.user.profile.log_action("issue_status_set", str(issue))

            else:
                messages.error(
                    request, result.get("error", "Failed to close issue on GitHub")
                )

        except Exception as e:
            messages.error(request, f"Error closing issue: {str(e)}")

        return redirect("issue-detail", pk=issue.pk)


class IssueModalView(DetailView):
    """View for returning a DaisyUI modal fragment (used by HTMX) to close an issue.

    Access rules:
    - Anonymous → 404 (not redirect)
    - Only superusers may access modal

    Querystring:
        ?action=addressed  (Green button, marks as addressed)
        ?action=wontfix    (Yellow button, marks as wontfix)

    Returns:
        - HTML fragment rendered from `{% partialdef close_modal_partial %}`
        - Never returns a full HTML page
        - Raises Http404 if action is invalid
    """

    model = Issue

    def get(self, request, *args, **kwargs):
        """
        HTMX-only modal endpoint.
        Only superusers may access.
        Raises Http404:
        - if user is not superuser
        - if ?action is invalid
        """
        if not request.user.is_superuser:
            raise Http404()  # ✅ now pytest can catch it

        action = request.GET.get("action")
        if action not in ("addressed", "wontfix"):
            raise Http404()  # ✅ now pytest catches as well

        issue = self.get_object()

        html = render_to_string(
            "core/issue_detail.html#close_modal_partial",
            {
                "issue": issue,
                "modal_id": f"close-{action}-modal",
                "action_value": action,
                "action_label": f"Close issue as {action}",
                "btn_class": "btn-success" if action == "addressed" else "btn-warning",
            },
            request=request,
        )

        return HttpResponse(html)


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
                Contribution.objects.get(id=self.contribution_id),
                self.request.user.profile,
            )
        else:
            data = {
                "priority": "medium priority",
                "issue_body": "Please provide issue description here.",
                "issue_title": "Issue title",
            }

        initial.update(data)
        return initial

    def get_context_data(self, *args, **kwargs):
        """Add contribution context data to template.

        :param kwargs: Additional keyword arguments
        :return: dict
        """
        context = super().get_context_data(*args, **kwargs)

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
        self.request.user.profile.log_action(
            "contribution_created", contribution.info()
        )
        add_reaction_to_message(contribution.url, DISCORD_EMOJIS.get("noted"))

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
