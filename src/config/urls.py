"""
URL Configuration for dailyword project.
"""

from django.contrib import admin
from django.http import HttpResponse
from django.urls import path

urlpatterns = [
    path("", lambda request: HttpResponse(), name="home"),
    path("admin/", admin.site.urls),
]
