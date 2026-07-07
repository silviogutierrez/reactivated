from django.urls import path

from tests import autocomplete

urlpatterns = [
    path("autocomplete-view/", autocomplete.autocomplete_view),
    path("typed-autocomplete-view/", autocomplete.typed_autocomplete_view),
]
