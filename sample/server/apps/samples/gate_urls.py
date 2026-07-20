from django.urls import include, path

urlpatterns = [
    path("gate/", include("sample.server.apps.samples.gate_router")),
]
