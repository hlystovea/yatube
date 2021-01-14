import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Paginator
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.author = User.objects.create(username='TestAuthor')
        cls.user = User.objects.create(username='TestUser')
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif',
        )
        for i in range(2):
            group = Group.objects.create(
                title=f'Группа{i}',
                slug=f'test-slug{i}',
                description=f'Тестовое сообщество {i}',
            )
            Post.objects.create(
                text=f'Тестовый пост необходимой длины {i}',
                author=cls.author,
                group=group,
                image=uploaded,
            )
        cls.post = Post.objects.create(
            text='Тестовый пост без группы',
            author=cls.author,
            image=uploaded,
        )

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.group_args = {'slug': Group.objects.get(pk=1).slug}
        cls.profile_args = {'username': cls.author.username}
        cls.post_args = {
            'username': cls.author.username,
            'post_id': cls.post.id
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адреса приложения posts используют соответствующие шаблоны."""
        urls = {
            'posts:index': ('posts/index.html', None),
            'posts:new_post': ('posts/post_form.html', None),
            'posts:group': ('group.html', self.group_args),
            'posts:profile': ('posts/profile.html', self.profile_args),
            'posts:post': ('posts/post.html', self.post_args),
        }
        for url_name, value in urls.items():
            with self.subTest(value=url_name):
                response = self.authorized_client.get(
                                    reverse(url_name, kwargs=value[1]))
                self.assertTemplateUsed(response, value[0])

    def test_post_edit_page_templates(self):
        """URL-адрес страницы редактирования поста использует
        соответствующий шаблон."""
        templates = {
            self.author_client: 'posts/post_form.html',
            self.authorized_client: 'posts/post.html',
        }
        for user, template in templates.items():
            with self.subTest(value=template):
                response = user.get(
                    reverse('posts:post_edit', kwargs=self.post_args),
                    follow=True,
                )
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        posts = Post.objects.all()
        paginator = Paginator(posts, 10)
        response = self.client.get(reverse('posts:index'))
        context_fields = {
            response.context['page'].object_list[0]: posts[0],
            response.context['paginator'].count: paginator.count,
        }
        for value, expected in context_fields.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        posts = self.author.posts.all()
        paginator = Paginator(posts, 10)
        response = self.client.get(
            reverse('posts:profile', kwargs=self.profile_args))
        context_fields = {
            response.context['page'].object_list[0]: posts[0],
            response.context['author']: self.author,
            response.context['paginator'].count: paginator.count,
        }
        for value, expected in context_fields.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_post_page_show_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:post', kwargs=self.post_args))
        context_fields = {
            'post': Post.objects.get(id=self.post.id),
            'author': self.author,
        }
        for value, expected in context_fields.items():
            with self.subTest(value=value):
                self.assertEqual(response.context[value], expected)

    def test_new_post_page_show_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:new_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertEqual(response.context['is_edit'], False)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse('posts:post_edit', kwargs=self.post_args))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertEqual(response.context['is_edit'], True)

    def test_group_pages_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        for group in Group.objects.all():
            with self.subTest(value=group):
                posts = group.posts.all()
                paginator = Paginator(posts, 10)
                response = self.client.get(
                    reverse('posts:group', kwargs={'slug': group.slug}))
                actual_post = response.context['page'].object_list[0]
                actual_group = response.context['group']
                actual_count = response.context['paginator'].count
                self.assertEqual(actual_post, posts[0])
                self.assertEqual(actual_group, group)
                self.assertEqual(actual_count, paginator.count)
                self.assertNotEqual(actual_post, Post.objects.get(group=None))


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.author = User.objects.create(username='TestUser')
        cls.group = Group.objects.create(
            title='Группа',
            slug='test-slug',
            description='Тестовое сообщество',
        )
        for i in range(13):
            Post.objects.create(
                text=f'Тестовый пост необходимой длины {i}',
                author=cls.author,
                group=cls.group)

        cls.group_args = {'slug': cls.group.slug}
        cls.profile_args = {'username': cls.author.username}

    def test_index_first_page_containse_ten_records(self):
        """Первые страницы паджинаторов содержат правильное кол-во записей."""
        urls = {
            'posts:index': (None, 10),
            'posts:group': (self.group_args, 10),
            'posts:profile': (self.profile_args, 10),
        }
        for url_name, value in urls.items():
            response = self.client.get(reverse(url_name, kwargs=value[0]))
            self.assertEqual(
                len(response.context['page'].object_list), value[1])

    def test_index_second_page_containse_three_records(self):
        """Вторые страницы паджинаторов содержат правильное кол-во записей."""
        urls = {
            'posts:index': (None, 3),
            'posts:group': (self.group_args, 3),
            'posts:profile': (self.profile_args, 3),
        }
        for url_name, value in urls.items():
            response = self.client.get(
                reverse(url_name, kwargs=value[0]) + '?page=2')
            self.assertEqual(
                len(response.context['page'].object_list), value[1])
