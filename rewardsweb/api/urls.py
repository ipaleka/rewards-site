from django.urls import path

from . import views

urlpatterns = [
    path('contributions', views.ContributionsView.as_view(), name='contributions'),
    path('cycles/aggregated', views.CycleAggregatedView.as_view(), name='cycle-aggregated'),
    path('cycles/dates/<int:cycle_id>', views.CycleDatesView.as_view(), name='cycle-dates'),
    path('contributions/last', views.ContributionsLastView.as_view(), name='contributions-last'),
    path('addcontribution', views.AddContributionView.as_view(), name='add-contribution'),
]