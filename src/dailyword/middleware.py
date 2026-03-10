from django.contrib.auth import login
from django.contrib.auth.models import User

HA_SUPERVISOR_IP = "172.30.32.2"


class IngressMiddleware:
    """Handle Home Assistant Ingress: IP-gated SCRIPT_NAME, auto-login, CSRF exemption, iframe."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        is_ingress = request.META.get("REMOTE_ADDR") == HA_SUPERVISOR_IP

        if not is_ingress:
            return self.get_response(request)

        # Set SCRIPT_NAME for correct URL generation in admin
        ingress_path = request.headers.get("x-ingress-path", "")
        if ingress_path:
            request.META["SCRIPT_NAME"] = ingress_path.rstrip("/")

        # HA already authenticates ingress requests
        request._dont_enforce_csrf_checks = True

        # Auto-login HA users
        username = request.headers.get("x-remote-user-name", "")
        if username and not (
            request.user.is_authenticated and request.user.username == username
        ):
            display_name = request.headers.get("x-remote-user-display-name", "")
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": display_name,
                    "is_staff": True,
                    "is_superuser": True,
                },
            )
            if not created:
                updates = []
                if not user.is_staff:
                    user.is_staff = True
                    updates.append("is_staff")
                if not user.is_superuser:
                    user.is_superuser = True
                    updates.append("is_superuser")
                if updates:
                    user.save(update_fields=updates)
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")

        response = self.get_response(request)

        # Allow iframe embedding for HA's UI
        response.headers.pop("X-Frame-Options", None)

        return response
