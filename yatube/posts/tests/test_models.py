from django.conf import settings
from django.test import TestCase

from ..models import Group, Post, User, Comment


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='leo')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test text',
        )
        cls.group = Group.objects.create(
            title='Hello world',
            slug='Test slug',
            description='Tortik',
        )

        cls.comment = Comment.objects.create(
            post=cls.post,
            text='Тестовый комментарий',
            author=cls.user,

        )

    def test_models_have_correct_post_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(
            f' Автор поста {self.post.author} '
            f' группы {self.post.group} написанный {self.post.pub_date} '
            f'с текстом {self.post.text[:settings.CUT_TEXT]}',
            str(self.post)
        )

    def test_models_have_correct_group_names(self):
        """Проверка заполнения str group"""
        self.assertEqual(str(self.group), self.group.title)

    def test_models_have_correct_comment_names(self):
        """Проверка заполнения str group"""
        self.assertEqual(
            f' Автор коммента {self.comment.author}'
            f' написанный {self.comment.created}'
            f' с текстом {self.comment.text[:settings.CUT_TEXT]}',
            str(self.comment))
