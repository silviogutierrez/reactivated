from django.urls import path

from . import views

urlpatterns = [
    path("", views.django_default, name="django_default"),
    path("polls/", views.polls_index, name="polls_index"),
    path("polls/create/", views.create_question, name="create_question"),
]
