from django.urls import path

from .views import DailyWordImageView

app_name = "dailyword"

urlpatterns = [
    path(
        "<str:dictionary_slug>/<int:width>x<int:height>/",
        DailyWordImageView.as_view(),
        name="daily-word-image",
    ),
]
