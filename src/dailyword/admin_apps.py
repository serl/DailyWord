from django.contrib.admin.apps import AdminConfig


class DailyWordAdminConfig(AdminConfig):
    default_site = "dailyword.admin_site.DailyWordAdminSite"
