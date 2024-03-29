import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Group, Post

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

        cls.author = User.objects.create(username='TestAuthor')
        cls.group = Group.objects.create(
            title='Тест',
            slug='test-slug',
            description='Тестовое сообщество',
        )
        cls.group_2 = Group.objects.create(
            title='Тест 2',
            slug='test-slug2',
            description='Тестовое сообщество 2',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост необходимой длины',
            author=cls.author,
            group=cls.group,
        )

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)

        cls.post_args = {
            'username': cls.author.username,
            'post_id': cls.post.id,
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def test_create_post_form(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
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
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:new_post'),
            data=form_data,
            follow=True,
        )
        is_post_exist = Post.objects.filter(text=form_data['text']).exists()

        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(is_post_exist)

    def test_post_edit_form(self):
        """Валидная форма редактирует запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Отредактированный тестовый текст',
            'group': self.group_2.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs=self.post_args),
            data=form_data,
        )
        post = Post.objects.get(id=self.post.id)
        self.assertRedirects(
            response, reverse('posts:post', kwargs=self.post_args),
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])


class CommentFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.author = User.objects.create(username='TestAuthor')
        cls.user = User.objects.create(username='TestUser')

        cls.post = Post.objects.create(text='Текст', author=cls.author)
        cls.comment = Comment.objects.create(
            text='Текст',
            author=cls.user,
            post=cls.post,
        )

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.post_args = {
            'username': cls.author.username,
            'post_id': cls.post.id,
        }
        cls.comm_args = {
            'username': cls.author.username,
            'post_id': cls.post.id,
            'comment_id': cls.comment.id,
        }

    def test_create_comment_form(self):
        """Валидная форма создает запись в Comment."""
        comments_count = Comment.objects.count()

        data = {'text': 'Комментарий'}

        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs=self.post_args),
            data=data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse('posts:post', kwargs=self.post_args),
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(Comment.objects.filter(text=data['text']).exists())

    def test_edit_comment_form(self):
        """Валидная форма редактирует запись в Comment."""
        comments_count = Comment.objects.count()

        data = {'text': 'Изменённый текст'}

        response = self.authorized_client.post(
            reverse('posts:comment_edit', kwargs=self.comm_args),
            data=data,
        )
        post = Comment.objects.get(id=self.comment.id)
        self.assertRedirects(
            response, reverse('posts:post', kwargs=self.post_args),
        )
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertEqual(post.text, data['text'])
