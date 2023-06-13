from django.urls import path

from . import views

urlpatterns = [
    path("", views.home_page, name="home_page"),
    path("install/", views.install, name="install"),
    path("install/<str:tag>/", views.install),
    path(
        "contributor-license-agreement/",
        views.documentation,
        {"page_name": "contributor-license-agreement"},
    ),
    path("documentation/<str:page_name>/", views.documentation, name="documentation"),
]
