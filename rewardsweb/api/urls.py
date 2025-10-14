from django.urls import path

from . import views

urlpatterns = [
    path('contributions', views.ContributionsView.as_view(), name='contributions'),
    path('cycles/current-plain', views.CurrentCyclePlainView.as_view(), name='cycle-current-plain'),
    path('cycles/current', views.CurrentCycleAggregatedView.as_view(), name='cycle-current'),
    path('cycles/<int:cycle_id>', views.CycleAggregatedView.as_view(), name='cycle-by-id'),
    path('contributions/last', views.ContributionsLastView.as_view(), name='contributions-last'),
    path('addcontribution', views.AddContributionView.as_view(), name='add-contribution'),
]