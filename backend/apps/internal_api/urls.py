from django.urls import path
from . import views

app_name = 'internal_api'

urlpatterns = [
    path('recommendations/suggest-today/', views.SuggestTodayView.as_view(), name='suggest-today'),
    path('tracking/context/', views.TrackingContextView.as_view(), name='tracking-context'),
    path('tracking/feedback/', views.TrackingFeedbackView.as_view(), name='tracking-feedback'),
    path('coach/summary/', views.CoachSummaryView.as_view(), name='coach-summary'),
    path('catalog/exercises/', views.CatalogExercisesView.as_view(), name='catalog-exercises'),
]
