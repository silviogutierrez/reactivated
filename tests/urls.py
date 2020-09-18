from django.urls import path

from tests import views

urlpatterns = [
    path("autocomplete-view/", views.autocomplete_view),
    path("typed-autocomplete-view/", views.typed_autocomplete_view),
]
