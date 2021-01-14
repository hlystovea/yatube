from django.test import TestCase
from django.urls import reverse


class StaticViewsTests(TestCase):
    def test_url_uses_correct_template(self):
        """URL-адреса приложения about используют правильный  шаблон."""
        templates = {
            'about:author': 'about/author.html',
            'about:tech': 'about/tech.html',
        }
        for url_name, template in templates.items():
            with self.subTest(value=url_name):
                response = self.client.get(reverse(url_name))
                self.assertTemplateUsed(response, template)
