"""Module containing website's URL configuration."""

from django.urls import path

from core import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("profile/", views.ProfileEditView.as_view(), name="profile"),
    path("cycles/", views.CycleListView.as_view(), name="cycles"),
    path("cycle/<int:pk>", views.CycleDetailView.as_view(), name="cycle-detail"),
    path("contributors/", views.ContributorListView.as_view(), name="contributors"),
    path(
        "contributor/<int:pk>",
        views.ContributorDetailView.as_view(),
        name="contributor-detail",
    ),
    path(
        "contribution/<int:pk>",
        views.ContributionDetailView.as_view(),
        name="contribution-detail",
    ),
    path(
        "contribution/<int:pk>/edit/",
        views.ContributionEditView.as_view(),
        name="contribution-edit",
    ),
    path(
        "contribution/<int:pk>/invalidate/<str:reaction>",
        views.ContributionInvalidateView.as_view(),
        name="contribution-invalidate",
    ),
    path("issues/", views.IssueListView.as_view(), name="issues"),
    path(
        "create-issue/<int:contribution_id>",
        views.CreateIssueView.as_view(),
        name="create-issue",
    ),
    path(
        "issue/<int:pk>",
        views.IssueDetailView.as_view(),
        name="issue-detail",
    ),
]
