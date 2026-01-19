from django.test import TestCase


class TestHome(TestCase):
    def test_home_returns_200(self):
        result = self.client.get("/")

        self.assertEqual(result.status_code, 200)
