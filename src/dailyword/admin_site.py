from django.contrib.admin import AdminSite


class DailyWordAdminSite(AdminSite):
    site_header = "DailyWord"
    site_title = "DailyWord"
    index_title = ""

    def each_context(self, request):
        context = super().each_context(request)
        is_ingress = getattr(request, "is_ingress", False)
        context["is_ingress"] = is_ingress

        return context

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label=app_label)
        if getattr(request, "is_ingress", False):
            # User management has no sense in ingress mode, since Home Assistant handles authentication and user management itself. So we hide the auth app.
            app_list = [app for app in app_list if app["app_label"] != "auth"]
        return app_list
