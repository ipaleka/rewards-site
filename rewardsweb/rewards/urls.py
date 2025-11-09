"""Module containing the URL configuration for the rewards app."""

from django.urls import path

from rewards import views

urlpatterns = [
    path("claim/", views.ClaimView.as_view(), name="claim"),
    path(
        "add-allocations/", views.AddAllocationsView.as_view(), name="add_allocations"
    ),
    path(
        "reclaim-allocations/",
        views.ReclaimAllocationsView.as_view(),
        name="reclaim_allocations",
    ),
]
