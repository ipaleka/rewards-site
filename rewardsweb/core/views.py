"""Module containing website's views."""

import logging

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Sum
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, FormView, ListView, UpdateView
from django.views.generic.detail import SingleObjectMixin

from core.forms import CreateIssueForm, ProfileFormSet, UpdateUserForm
from core.models import Contribution, Contributor, Cycle, Issue
from utils.issues import issue_data_for_contribution

logger = logging.getLogger(__name__)


class IndexView(ListView):
    model = Contribution
    paginate_by = 20
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

    def get_queryset(self):
        return Contribution.objects.filter(confirmed=False).reverse()


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


@method_decorator(user_passes_test(lambda user: user.is_superuser), name="dispatch")
class CreateIssueView(FormView):
    """TODO: docstring and tests"""

    template_name = "create_issue.html"
    form_class = CreateIssueForm

    def get(self, request, *args, **kwargs):
        # Store the initial ID from URL when the form is first loaded
        self.contribution_id = kwargs.get("contribution_id")
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Store the initial ID from URL when form is submitted
        self.contribution_id = kwargs.get("contribution_id")
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy("contribution-detail", args=[self.contribution_id])

    def get_initial(self):
        """Set initial data using the separate method"""
        initial = super().get_initial()

        if self.contribution_id:
            data = issue_data_for_contribution(
                Contribution.objects.get(id=self.contribution_id)
            )

        else:
            data["priority"] = "medium priority"
            data["issue_body"] = "Please provide your description here."
            data["issue_title"] = "default-value"

        initial.update(data)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add your variables to context - these will be used for initial values
        context["contribution_id"] = self.contribution_id

        # You can add any other variables you want to use
        context["page_title"] = f"Form for ID {self.contribution_id}"
        context["current_date"] = "2024-01-01"  # Example dynamic data

        # Add any calculation results from previous submission
        if "calculation_result" in self.request.session:
            context["calculation_result"] = self.request.session.pop(
                "calculation_result"
            )
            context["submitted_data"] = self.request.session.pop("submitted_data", {})

        return context

    def form_valid(self, form):
        # Your existing form validation logic
        cleaned_data = form.cleaned_data
        calculated_value = self.your_calculation_function(
            cleaned_data, self.contribution_id
        )

        self.request.session["calculation_result"] = calculated_value
        self.request.session["submitted_data"] = {
            "selected_labels": cleaned_data.get("multiple_labels", []),
            "text_preview": (
                cleaned_data.get("issue_body", "")[:50] + "..."
                if cleaned_data.get("issue_body")
                else ""
            ),
            "input_value": cleaned_data.get("issue_title", ""),
            "contribution_id": self.contribution_id,
        }

        return super().form_valid(form)

    def your_calculation_function(self, form_data, contribution_id):
        # Your existing calculation logic
        selected_labels = form_data.get("multiple_labels", [])
        priority = form_data.get("priority", "")
        issue_body = form_data.get("issue_body", "")
        issue_title = form_data.get("issue_title", "")

        result = {
            "contribution_id": contribution_id,
            "priority": priority,
            "total_categories": len(selected_labels),
            "text_length": len(issue_body),
            "processed_input": issue_title.upper(),
            "categories": selected_labels,
            "combined_result": f"ID-{contribution_id}-{priority}-{issue_title}-{len(selected_labels)}cats",
        }

        return result
