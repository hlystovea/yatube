from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Comment, Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = User.objects.create(username='TestUser')
        cls.group = Group.objects.create(
            title='Тест',
            slug='test-slug',
            description='Тестовое сообщество',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост необходимой длины',
            author=cls.user,
            group=cls.group,
        )

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            'text': 'Текст записи',
            'group': 'Сообщество',
            'image': 'Изображение',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    self.post._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        field_help_texts = {
            'text': 'Напишите что-нибудь.',
            'group': 'Выберите сообщество (необязательно)',
            'image': 'Добавьте изображение (необязательно)',
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    self.post._meta.get_field(value).help_text, expected)

    def test_object_name_is_text_field(self):
        """__str__.post - это строчка с содержимым post.text."""
        self.assertEquals(self.post.text[:15], str(self.post))

    def test_delete_user_with_post(self):
        posts_count = Post.objects.count()
        self.user.delete()
        self.assertNotEqual(posts_count, Post.objects.count())


class GroupModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.group = Group.objects.create(
            title='Тест',
            slug='test-slug',
            description='Тестовое сообщество',
        )

    def test_object_name_is_title_field(self):
        """__str__.group - это строчка с содержимым group.title."""
        self.assertEquals(self.group.title, str(self.group))


class CommentModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = User.objects.create(username='TestUser')

        cls.post = Post.objects.create(text='Текст', author=cls.user)
        cls.comment = Comment.objects.create(
            text='Текст',
            author=cls.user,
            post=cls.post,
        )

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            'post': 'Пост',
            'text': 'Комментарий',
            'created': 'Дата публикации',
            'author': 'Автор',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    self.comment._meta.get_field(value).verbose_name, expected)

    def test_delete_post_with_comment(self):
        comments_count = Comment.objects.count()
        self.post.delete()
        self.assertNotEqual(comments_count, Comment.objects.count())
