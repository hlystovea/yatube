from django.test import TestCase
from django.urls import reverse


class StaticURLTests(TestCase):
    def test_url_name_matches_desired_address(self):
        """URL-имена приложения about соответствуют ожидаемым адресам."""
        url_names = {
            'about:author': '/about/author/',
            'about:tech': '/about/tech/',
        }
        for url_name, url in url_names.items():
            with self.subTest(value=url_name):
                self.assertEqual(reverse(url_name), url)

    def test_url_exists_at_desired_location(self):
        """Проверка доступности адресов приложения about."""
        urls = {
            'about:author': 200,
            'about:tech': 200,
        }
        for url, status_code in urls.items():
            with self.subTest(value=url):
                response = self.client.get(reverse(url))
                self.assertEqual(response.status_code, status_code)
