from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Post(models.Model):
    text = models.TextField(
        verbose_name='Текст записи',
        help_text='Напишите что-нибудь.',
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
    )
    author = models.ForeignKey(
        to=User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='posts',
    )
    group = models.ForeignKey(
        to='Group',
        verbose_name='Сообщество',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='posts',
        help_text='Выберите сообщество (необязательно)',
    )
    image = models.ImageField(
        upload_to='posts/',
        verbose_name='Изображение',
        blank=True,
        null=True,
        help_text='Добавьте изображение (необязательно)'
    )

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return self.text[:15]


class Group(models.Model):
    title = models.CharField(
        verbose_name='Сообщество',
        max_length=200,
        unique=True,
    )
    slug = models.SlugField(max_length=30, unique=True)
    description = models.TextField(max_length=300)

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(
        to='Post',
        verbose_name='Пост',
        on_delete=models.CASCADE,
        related_name='comments',
    )
    text = models.TextField(
        verbose_name='Комментарий',
        max_length=300,
    )
    created = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
    )
    author = models.ForeignKey(
        to=User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='comments',
    )

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='following',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='user_and_author_uniq_together'),
            ]
