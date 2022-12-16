from django.conf import settings
from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='leo')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test text',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(
            str(self.post),
            self.post.text[:settings.CUT_TEXT]
        )


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Hello world',
            slug='Test slug',
            description='Tortik',
        )

    def test_models_have_correct_title_names(self):
        """Проверка заполнения str group"""
        self.assertEqual(str(self.group), self.group.title)
