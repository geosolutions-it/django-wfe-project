from django.urls import path
from django_wfe_integration.views import MyView


urlpatterns = [
    path('job/', MyView.as_view()),
]
