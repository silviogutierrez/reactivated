from django.urls import path

from . import views

urlpatterns = [
    path("", views.django_default, name="django_default"),
    path("polls/", views.polls_index, name="polls_index"),
    path("polls/<int:question_id>/", views.poll_detail, name="poll_detail"),
    path("polls/<int:question_id>/update/", views.update_poll, name="update_poll"),
    path("polls/<int:question_id>/vote/", views.vote, name="vote"),
    path("polls/<int:question_id>/results/", views.results, name="results"),
    path("polls/create/", views.create_poll, name="create_poll"),
]
