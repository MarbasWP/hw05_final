from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()
TEXT_POST = (
    'Автор поста {} группы {} '
    'написанный {} '
    'с текстом {:.15}')
TEXT_COMMENT = (
    'Автор коммента {} '
    'написанный {} с текстом {:.15}'
)
TEXT_FOLLOW = (
    '{} подписался на {}'
)


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='Заголовок'
    )
    slug = models.SlugField(
        max_length=30,
        unique=True,
        verbose_name='Уникальный фрагмент'
    )
    description = models.TextField(
        verbose_name='Описание'
    )

    class Meta:
        verbose_name = 'Сообщество'
        verbose_name_plural = 'Сообщества'

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        verbose_name='Текст'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        Group,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Сообщество'
    )
    image = models.ImageField(
        upload_to='posts/',
        blank=True,
        help_text='Добавить картинку',
        verbose_name='Картинка'
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return TEXT_POST.format(
            self.author, self.group,
            self.pub_date, self.text)


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Запись'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор комментария'
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Введите текст комментария'
    )
    created = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return (
            TEXT_COMMENT.format(self.author, self.created, self.text))


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписчик'
        verbose_name_plural = 'Подписчики'

    def __str__(self):
        return TEXT_FOLLOW.format(str(self.user), self.author)
