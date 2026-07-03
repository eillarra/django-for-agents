"""URL definitions for django_for_agents."""

from django.urls import path

from .llms import LlmsTxtView

urlpatterns = [
    path("llms.txt", LlmsTxtView.as_view(), name="for_agents_llms_txt"),
]
