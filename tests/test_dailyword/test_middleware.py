import pytest
from django.contrib import admin
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import Client
from django.urls import path

from dailyword.middleware import HA_SUPERVISOR_IP

urlpatterns = [
    path("", lambda request: HttpResponse(), name="home"),
    path("admin/", admin.site.urls),
]

INGRESS_HEADERS = {
    "REMOTE_ADDR": HA_SUPERVISOR_IP,
    "HTTP_X_INGRESS_PATH": "/api/hassio_ingress/abc123",
    "HTTP_X_REMOTE_USER_NAME": "hauser",
    "HTTP_X_REMOTE_USER_DISPLAY_NAME": "HA User",
}


@pytest.fixture(autouse=True)
def _ingress_test_setup(settings):
    settings.ROOT_URLCONF = "tests.test_dailyword.test_middleware"
    settings.HOME_ASSISTANT_INGRESS_ENABLED = True


@pytest.fixture
def client():
    return Client()


class TestIPGating:
    def test_ignores_ingress_headers_from_untrusted_ip(self, client, db):
        response = client.get(
            "/",
            HTTP_X_INGRESS_PATH="/api/hassio_ingress/abc123",
            HTTP_X_REMOTE_USER_NAME="hauser",
        )
        assert "X-Frame-Options" in response
        assert not User.objects.filter(username="hauser").exists()

    def test_activates_for_trusted_ip(self, client, db):
        response = client.get("/", **INGRESS_HEADERS)
        assert "X-Frame-Options" not in response
        assert User.objects.filter(username="hauser").exists()


class TestScriptName:
    def test_sets_script_name_from_header(self, client, db):
        response = client.get("/", **INGRESS_HEADERS)
        assert response.status_code == 200

    def test_strips_trailing_slash(self, client, db):
        headers = {
            **INGRESS_HEADERS,
            "HTTP_X_INGRESS_PATH": "/api/hassio_ingress/abc123/",
        }
        response = client.get("/", **headers)
        assert response.status_code == 200

    def test_no_script_name_without_ingress_path(self, client, db):
        headers = {
            k: v for k, v in INGRESS_HEADERS.items() if k != "HTTP_X_INGRESS_PATH"
        }
        response = client.get("/", **headers)
        assert response.status_code == 200


class TestAutoLogin:
    def test_creates_user_with_staff_and_superuser(self, client, db):
        client.get("/", **INGRESS_HEADERS)

        user = User.objects.get(username="hauser")
        assert user.first_name == "HA User"
        assert user.is_staff
        assert user.is_superuser

    def test_skips_login_if_already_logged_in(self, client, db):
        # First request creates and logs in the user
        client.get("/", **INGRESS_HEADERS)
        # Second request should skip login (user already authenticated)
        client.get("/", **INGRESS_HEADERS)

        assert User.objects.filter(username="hauser").count() == 1

    def test_no_user_created_without_username_header(self, client, db):
        headers = {
            k: v for k, v in INGRESS_HEADERS.items() if k != "HTTP_X_REMOTE_USER_NAME"
        }
        client.get("/", **headers)

        assert User.objects.count() == 0


class TestXFrameOptions:
    def test_removed_for_ingress(self, client, db):
        response = client.get("/", **INGRESS_HEADERS)
        assert "X-Frame-Options" not in response

    def test_kept_for_direct_access(self, client, db):
        response = client.get("/")
        assert "X-Frame-Options" in response


class TestCSRF:
    @pytest.fixture
    def csrf_client(self):
        return Client(enforce_csrf_checks=True)

    def test_post_allowed_through_ingress(self, csrf_client, db):
        response = csrf_client.post(
            "/admin/login/", {"username": "x", "password": "y"}, **INGRESS_HEADERS
        )
        assert response.status_code != 403

    def test_post_blocked_without_ingress(self, csrf_client, db):
        response = csrf_client.post("/admin/login/", {"username": "x", "password": "y"})
        assert response.status_code == 403


class TestDisabledByDefault:
    """Verify the middleware has no effect when HOME_ASSISTANT_INGRESS_ENABLED is False."""

    @pytest.fixture(autouse=True)
    def _without_ingress_enabled(self, settings):
        settings.HOME_ASSISTANT_INGRESS_ENABLED = False

    def test_ingress_headers_ignored_when_disabled(self, client, db):
        response = client.get("/", **INGRESS_HEADERS)
        assert "X-Frame-Options" in response
        assert not User.objects.filter(username="hauser").exists()
