import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Paginator
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post

User = get_user_model()


class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

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
            post = Post.objects.create(
                text=f'Тестовый пост необходимой длины {i}',
                author=cls.author,
                group=group,
                image=uploaded,
            )
            post.save()
        cls.post = Post.objects.create(
            text='Тестовый пост без группы',
            author=cls.author,
            image=uploaded,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            text='Комментарий',
            author=cls.author,
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.group_args = {'slug': Group.objects.get(pk=1).slug}
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адреса приложения posts используют соответствующие шаблоны."""
        urls = {
            'posts:index': ('posts/index.html', None),
            'posts:new_post': ('posts/post_form.html', None),
            'posts:group': ('posts/group.html', self.group_args),
            'posts:profile': ('posts/profile.html', self.profile_args),
            'posts:post': ('posts/post.html', self.post_args),
            'posts:follow_index': ('posts/follow.html', None),
            'posts:profile_follow': ('posts/profile.html', self.profile_args),
            'posts:profile_unfollow': ('posts/profile.html', self.profile_args), # noqa
        }
        for url_name, value in urls.items():
            with self.subTest(value=url_name):
                response = self.authorized_client.get(
                    reverse(url_name, kwargs=value[1]),
                    follow=True,
                )
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

    def test_index_page_posts_cache(self):
        """Авторизованный пользователь получает посты на странице index
        из кеша."""
        response1 = self.authorized_client.get(reverse('posts:index'))
        html1 = response1.content.decode()
        post1 = Post.objects.filter(id=self.post.id)[0]

        Post.objects.filter(id=self.post.id).update(text='Другой текст')

        response2 = self.authorized_client.get(reverse('posts:index'))
        html2 = response2.content.decode()
        post2 = Post.objects.filter(id=self.post.id)[0]

        self.assertNotEqual(post1.text, post2.text)
        self.assertHTMLEqual(html1, html2)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        posts = self.author.posts.all()
        paginator = Paginator(posts, 10)
        response = self.client.get(
            reverse('posts:profile', kwargs=self.profile_args),
        )
        context_fields = {
            response.context['page'].object_list[0]: posts[0],
            response.context['author']: self.author,
            response.context['paginator'].count: paginator.count,
            response.context['is_follow']: False,
        }
        for value, expected in context_fields.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_post_page_show_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:post', kwargs=self.post_args),
        )
        context_fields = {
            'post': Post.objects.get(id=self.post.id),
            'author': self.author,
            'is_follow': False,
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
            reverse('posts:post_edit', kwargs=self.post_args),
        )
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
        self.assertEqual(response.context['post'], self.post)

    def test_add_comment_page_show_correct_context(self):
        """Шаблон add_comment сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse('posts:add_comment', kwargs=self.post_args),
        )
        form_field = response.context['form'].fields['text']
        comments_count = response.context['comments'].count()
        context_fields = {
            'post': Post.objects.get(id=self.post.id),
            'is_follow': False,
        }
        for value, expected in context_fields.items():
            with self.subTest(value=value):
                self.assertEqual(response.context[value], expected)
        self.assertIsInstance(form_field, forms.fields.CharField)
        self.assertEqual(comments_count, self.post.comments.count())

    def test_comment_edit_page_show_correct_context(self):
        """Шаблон comment_edit сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse('posts:comment_edit', kwargs=self.comm_args),
        )
        form_field = response.context['form'].fields['text']
        comments_count = response.context['comments'].count()
        context_fields = {
            'post': Post.objects.get(id=self.post.id),
            'comment_id': self.comment.id,
            'is_follow': False,
        }
        for value, expected in context_fields.items():
            with self.subTest(value=value):
                self.assertEqual(response.context[value], expected)
        self.assertIsInstance(form_field, forms.fields.CharField)
        self.assertEqual(comments_count, self.post.comments.count())

    def test_group_pages_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        for group in Group.objects.all():
            with self.subTest(value=group):
                posts = group.posts.all()
                paginator = Paginator(posts, 10)
                response = self.client.get(
                    reverse('posts:group', kwargs={'slug': group.slug}),
                )
                actual_post = response.context['page'].object_list[0]
                actual_group = response.context['group']
                actual_count = response.context['paginator'].count
                self.assertEqual(actual_post, posts[0])
                self.assertEqual(actual_group, group)
                self.assertEqual(actual_count, paginator.count)
                self.assertNotEqual(actual_post, Post.objects.get(group=None))

    def test_authorized_user_follow_author(self):
        """Авторизованный пользователь может подписываться
        на других авторов."""
        url = reverse('posts:profile_follow', kwargs=self.profile_args)
        users = {
            1: (self.client, 0),
            2: (self.author_client, 0),
            3: (self.authorized_client, 1),
            4: (self.authorized_client, 1),
        }
        for number, value in users.items():
            with self.subTest(value=number):
                response = value[0].get(url) # noqa
                self.assertEqual(self.author.following.count(), value[1])

    def test_authorized_user_unfollow_author(self):
        """Авторизованный пользователь может отписываться от других авторов."""
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs=self.profile_args),
        )
        url = reverse('posts:profile_unfollow', kwargs=self.profile_args)
        users = {
            1: (self.client, 1),
            2: (self.author_client, 1),
            3: (self.authorized_client, 0),
            4: (self.authorized_client, 0),
        }
        for number, value in users.items():
            with self.subTest(value=number):
                response = value[0].get(url) # noqa
                self.assertEqual(self.author.following.count(), value[1])

    def test_only_authorized_user_add_comment(self):
        """Только авторизованный пользователь может добавлять комментарии."""
        comments_count = Comment.objects.count()
        path = reverse('posts:add_comment', kwargs=self.post_args)
        data = {'text': 'Комментарий'}

        self.client.post(path, data, follow=True)
        self.assertEqual(Comment.objects.count(), comments_count)

        self.authorized_client.post(path, data, follow=True)
        self.assertEqual(Comment.objects.count(), comments_count + 1)

    def test_only_authorized_author_comment_del(self):
        """Только авторизованный автор может удалять комментарии."""
        comments_count = Comment.objects.count()
        path = reverse('posts:comment_del', kwargs=self.comm_args)

        self.authorized_client.post(path, follow=True)
        self.assertEqual(Comment.objects.count(), comments_count)

        self.author_client.post(path, follow=True)
        self.assertEqual(Comment.objects.count(), comments_count - 1)

    def test_only_authorized_author_post_del(self):
        """Только авторизованный автор может удалять посты."""
        posts_count = Post.objects.count()
        path = reverse('posts:post_del', kwargs=self.post_args)

        self.authorized_client.post(path, follow=True)
        self.assertEqual(Post.objects.count(), posts_count)

        self.author_client.post(path, follow=True)
        self.assertEqual(Post.objects.count(), posts_count - 1)


class FollowPageTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user1 = User.objects.create(username='TestUser1')
        cls.user2 = User.objects.create(username='TestUser2')
        cls.user3 = User.objects.create(username='TestUser3')

        Post.objects.create(text='Пост', author=cls.user3)
        Follow.objects.create(user=cls.user1, author=cls.user3)

        cls.follower = Client()
        cls.follower.force_login(cls.user1)

        cls.not_follower = Client()
        cls.not_follower.force_login(cls.user2)

        cls.author = Client()
        cls.author.force_login(cls.user3)

    def test_follow_page_show_relevant_posts(self):
        """Новая запись автора появляется в ленте тех, кто на него подписан."""
        response1 = self.follower.get(reverse('posts:follow_index'))
        response2 = self.not_follower.get(reverse('posts:follow_index'))
        posts_count1 = response1.context['paginator'].count
        posts_count2 = response2.context['paginator'].count

        Post.objects.create(text='Пост для теста', author=self.user3)

        response3 = self.follower.get(reverse('posts:follow_index'))
        response4 = self.not_follower.get(reverse('posts:follow_index'))
        posts_count3 = response3.context['paginator'].count
        posts_count4 = response4.context['paginator'].count

        self.assertNotEqual(posts_count1, posts_count3)
        self.assertEqual(posts_count2, posts_count4)


class PaginatorsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.author = User.objects.create(username='TestUser')
        cls.group = Group.objects.create(
            title='Группа',
            slug='test-slug',
            description='Тестовое сообщество',
        )
        posts = []
        for i in range(13):
            post = Post(
                text=f'Тестовый пост необходимой длины {i}',
                author=cls.author,
                group=cls.group,
            )
            posts.append(post)
        Post.objects.bulk_create(posts)

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
            posts_page1_count = len(response.context['page'].object_list)
            self.assertEqual(posts_page1_count, value[1])

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
            posts_page2_count = len(response.context['page'].object_list)
            self.assertEqual(posts_page2_count, value[1])
