"""
URL Configuration for dailyword project.
"""

from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path

admin.site.site_header = "DailyWord"
admin.site.site_title = "DailyWord"
admin.site.index_title = ""

urlpatterns = [
    path("", lambda request: HttpResponse(), name="home"),
    path("admin/", admin.site.urls),
    path("", include("dailyword.urls")),
]
