from django.urls import path

from . import views

urlpatterns = [
    path("", views.django_default, name="django_default"),
]
