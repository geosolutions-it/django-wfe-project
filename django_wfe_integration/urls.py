from django.urls import path
from django_wfe_integration.views import MyView, MyOtherView


urlpatterns = [
    path('job/', MyView.as_view()),
    path('job/<int:job>', MyOtherView.as_view())
]
