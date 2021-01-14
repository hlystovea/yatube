from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.author = User.objects.create(username='TestAuthor')
        cls.user = User.objects.create(username='TestUser')
        cls.group = Group.objects.create(
            title='Тест',
            slug='test-slug',
            description='Тестовое сообщество',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост необходимой длины',
            author=cls.author,
            group=cls.group,
        )

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.group_args = {'slug': cls.group.slug}
        cls.profile_args = {'username': cls.author.username}
        cls.post_args = {
            'username': cls.author.username,
            'post_id': cls.post.id
        }

    def test_url_name_matches_desired_address(self):
        """URL-имена приложения posts соответствуют ожидаемым адресам."""
        urls = {
            'posts:index': (None, '/'),
            'posts:new_post': (None, '/new/'),
            'posts:group': (self.group_args, f'/group/{self.group.slug}/'),
            'posts:profile': (self.profile_args, f'/{self.author.username}/'),
            'posts:post': (self.post_args, f'/{self.author.username}/{self.post.id}/'),
            'posts:post_edit': (self.post_args, f'/{self.author.username}/{self.post.id}/edit/'),
        }
        for url_name, value in urls.items():
            with self.subTest(value=url_name):
                self.assertEqual(reverse(url_name, kwargs=value[0]), value[1])

    def test_url_available_all_user(self):
        """Неавторизованному пользователю доступны соовтетствующие страницы."""
        urls = {
            'posts:index': (None, 200),
            'posts:new_post': (None, 302),
            'posts:group': (self.group_args, 200),
            'posts:profile': (self.profile_args, 200),
            'posts:post': (self.post_args, 200),
            'posts:post_edit': (self.post_args, 302),
        }
        for url_name, value in urls.items():
            with self.subTest(value=url_name):
                response = self.client.get(reverse(url_name, kwargs=value[0]))
                self.assertEqual(response.status_code, value[1])

    def test_url_available_authorized_user(self):
        """Авторизованному пользователю доступны соовтетствующие страницы."""
        urls = {
            'posts:index': (None, 200),
            'posts:new_post': (None, 200),
            'posts:group': (self.group_args, 200),
            'posts:profile': (self.profile_args, 200),
            'posts:post': (self.post_args, 200),
            'posts:post_edit': (self.post_args, 302),
        }
        for url_name, value in urls.items():
            with self.subTest(value=url_name):
                response = self.authorized_client.get(
                                    reverse(url_name, kwargs=value[0]))
                self.assertEqual(response.status_code, value[1])

    def test_url_available_authorized_author_post(self):
        """Авторизованному автору постов доступны соовтетствующие страницы."""
        urls = {
            reverse('posts:post_edit', kwargs=self.post_args): 200,
        }
        for url, status_code in urls.items():
            with self.subTest(value=url):
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, status_code)

    def test_url_errors_page(self):
        """Любому пользователю доступны страницы с ошибками."""
        urls = {
            '/some-name/': 404,
        }
        for url, status_code in urls.items():
            with self.subTest(value=url):
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, status_code)
