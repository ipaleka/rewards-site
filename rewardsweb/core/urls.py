from django.urls import path

from core import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("cycles/", views.CycleListView.as_view(), name="cycles"),
    path("cycle/<int:pk>", views.CycleDetailView.as_view(), name="cycle-detail"),
    path("contributors/", views.ContributorListView.as_view(), name="contributors"),
    path(
        "contributor/<int:pk>",
        views.ContributorDetailView.as_view(),
        name="contributor-detail",
    ),
]
