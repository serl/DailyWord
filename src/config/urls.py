"""
URL Configuration for dailyword project.
"""

from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path

urlpatterns = [
    path("", lambda request: HttpResponse(), name="home"),
    path("admin/", admin.site.urls),
    path("", include("dailyword.urls")),
]
