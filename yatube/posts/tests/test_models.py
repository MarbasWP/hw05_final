from django.test import TestCase
from django.conf import settings

from ..models import Group, Post, User, Comment, Follow

TEXT_POST = (
    'Автор поста {author} группы {group} '
    'написанный {pub_date} '
    'с текстом {text}')
TEXT_COMMENT = (
    'Автор коммента {author} '
    'написанный {created} с текстом {text}'
)
TEXT_FOLLOW = (
    '{user} подписался на {author}'
)


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='leo')
        cls.user2 = User.objects.create_user(username='marbas')
        cls.group = Group.objects.create(
            title='Hello world',
            slug='Тестовый комментарий',
            description='Tortik',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый комментарий',
            group=cls.group,
            pub_date='20.12.2022'
        )

        cls.comment = Comment.objects.create(
            post=cls.post,
            text='Тестовый комментарий',
            author=cls.user,
            created='20.12.2022',

        )
        cls.follow = Follow.objects.create(
            user=cls.user2,
            author=cls.user
        )

    def test_models_have_correct_post_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(
            TEXT_POST.format(
                author=self.post.author.username,
                group=self.post.group, pub_date=self.post.pub_date,
                text=self.post.text[:settings.CUT_TEXT]), str(self.post))

    def test_models_have_correct_group_names(self):
        """Проверка заполнения str group"""
        self.assertEqual(str(self.group), self.group.title)

    def test_models_have_correct_comment_names(self):
        """Проверка заполнения str group"""
        self.assertEqual(
            TEXT_COMMENT.format(
                author=self.comment.author.username,
                created=self.comment.created,
                text=self.comment.text[:settings.CUT_TEXT]),
            str(self.comment))

    def test_models_have_correct_follow_names(self):
        """Проверка заполнения str group"""
        self.assertEqual(
            TEXT_FOLLOW.format(
                user=self.follow.user.username,
                author=self.follow.author.username),
            str(self.follow))
