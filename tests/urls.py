from django.urls import path

from tests import views

urlpatterns = [path("autocomplete-view/", views.autocomplete_view)]
