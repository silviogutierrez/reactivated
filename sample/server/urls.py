"""server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from . import views
from .apps.samples import views as samples

urlpatterns = [
    path("admin/", admin.site.urls),
    path("hello-world/", views.hello_world),
    path("sample-form/", views.sample_form),
    path("composers/", samples.composer_list),
    path("composers/create/", samples.create_composer),
    path("operas/create/", samples.create_opera),
    path("browser/", samples.data_browser),
]