from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.urls import set_script_prefix

HA_SUPERVISOR_IP = "172.30.32.2"


class IngressMiddleware:
    """Handle Home Assistant Ingress: IP-gated SCRIPT_NAME, auto-login, CSRF exemption, iframe."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        is_ingress = (
            settings.HOME_ASSISTANT_INGRESS_ENABLED
            and request.META.get("REMOTE_ADDR") == HA_SUPERVISOR_IP
        )
        request.is_ingress = is_ingress

        if not is_ingress:
            return self.get_response(request)

        # Set script prefix for correct URL generation (reverse(), {% url %}, {% static %})
        set_script_prefix(request.headers.get("x-ingress-path", ""))

        # HA already authenticates ingress requests
        request._dont_enforce_csrf_checks = True

        # Auto-login HA users
        username = request.headers.get("x-remote-user-name", "")
        if username and not (
            request.user.is_authenticated and request.user.username == username
        ):
            display_name = request.headers.get("x-remote-user-display-name", "")
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": display_name,
                    "is_staff": True,
                    "is_superuser": True,
                },
            )

            login(request, user, backend="django.contrib.auth.backends.ModelBackend")

        response = self.get_response(request)

        # Allow iframe embedding for HA's UI
        response.headers.pop("X-Frame-Options", None)

        return response
