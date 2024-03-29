from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
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
        cls.comment = Comment.objects.create(
            text='Текст',
            author=cls.author,
            post=cls.post,
        )

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.group_args = {'slug': cls.group.slug}
        cls.profile_args = {'username': cls.author.username}
        cls.post_args = {
            'username': cls.author.username,
            'post_id': cls.post.id,
        }
        cls.comm_args = {
            'username': cls.author.username,
            'post_id': cls.post.id,
            'comment_id': cls.comment.id,
        }

    def test_url_name_matches_desired_address(self):
        """URL-имена приложения posts соответствуют ожидаемым адресам."""
        urls = {
            'posts:index': (None, '/'),
            'posts:new_post': (None, '/new/'),
            'posts:group': (self.group_args, f'/group/{self.group.slug}/'),
            'posts:profile': (self.profile_args, f'/{self.author.username}/'),
            'posts:post': (self.post_args, f'/{self.author.username}/{self.post.id}/'), # noqa
            'posts:post_edit': (self.post_args, f'/{self.author.username}/{self.post.id}/edit/'), # noqa
            'posts:post_del': (self.post_args, f'/{self.author.username}/{self.post.id}/del/'), # noqa
            'posts:follow_index': (None, '/follow/'),
            'posts:profile_follow': (self.profile_args, f'/{self.author.username}/follow/'), # noqa
            'posts:profile_unfollow': (self.profile_args, f'/{self.author.username}/unfollow/'), # noqa
            'posts:add_comment': (self.post_args, f'/{self.author.username}/{self.post.id}/comment/'), # noqa
            'posts:comment_edit': (self.comm_args, f'/{self.author.username}/{self.post.id}/comment/{self.comment.id}/edit/'), # noqa
            'posts:comment_del': (self.comm_args, f'/{self.author.username}/{self.post.id}/comment/{self.comment.id}/del/'), # noqa
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
            'posts:post_del': (self.post_args, 405),
            'posts:follow_index': (None, 302),
            'posts:profile_follow': (self.profile_args, 302),
            'posts:profile_unfollow': (self.profile_args, 302),
            'posts:add_comment': (self.post_args, 302),
            'posts:comment_edit': (self.comm_args, 302),
            'posts:comment_del': (self.comm_args, 405),
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
            'posts:post_del': (self.post_args, 405),
            'posts:follow_index': (None, 200),
            'posts:profile_follow': (self.profile_args, 302),
            'posts:profile_unfollow': (self.profile_args, 302),
            'posts:add_comment': (self.post_args, 200),
            'posts:comment_edit': (self.comm_args, 302),
            'posts:comment_del': (self.comm_args, 405),
        }
        for url_name, value in urls.items():
            with self.subTest(value=url_name):
                response = self.authorized_client.get(
                                    reverse(url_name, kwargs=value[0]),
                                )
                self.assertEqual(response.status_code, value[1])

    def test_url_available_authorized_author_post(self):
        """Авторизованному автору поста доступны соовтетствующие страницы."""
        urls = {
            1: ('posts:post_edit', self.post_args, 200),
            2: ('posts:comment_edit', self.comm_args, 200),
            3: ('posts:comment_del', self.comm_args, 405),
            4: ('posts:post_del', self.post_args, 405),
        }
        for value in urls.values():
            with self.subTest(value=value[0]):
                response = self.author_client.get(
                                    reverse(value[0], kwargs=value[1]),
                                )
                self.assertEqual(response.status_code, value[2])

    def test_comment_del_post_del_urls_available(self):
        """Cтраницы удаления поста и комментария доступны при POST запросе."""
        urls = {
            1: ('posts:comment_del', self.comm_args, 302),
            2: ('posts:post_del', self.post_args, 302),
        }
        for value in urls.values():
            with self.subTest(value=value[0]):
                response = self.client.post(
                                    reverse(value[0], kwargs=value[1]),
                                )
                self.assertEqual(response.status_code, value[2])

    def test_url_errors_page(self):
        """Любому пользователю доступны страницы с ошибками."""
        urls = {
            '/some-name/': 404,
        }
        for url, status_code in urls.items():
            with self.subTest(value=url):
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, status_code)
