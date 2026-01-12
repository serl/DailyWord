from django.test import SimpleTestCase


class TestStaticRoot(SimpleTestCase):
    def test_static_root_contents(self):
        result = self.client.get("/robots.txt")

        self.assertEqual(result.status_code, 200)
