from django.test import TestCase

from ..models import Group, Post, User, Comment, Follow

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
            TEXT_POST.format(str(self.post.author),
                             self.post.group, self.post.pub_date,
                             self.post.text), str(self.post))

    def test_models_have_correct_group_names(self):
        """Проверка заполнения str group"""
        self.assertEqual(str(self.group), self.group.title)

    def test_models_have_correct_comment_names(self):
        """Проверка заполнения str group"""
        self.assertEqual(
            TEXT_COMMENT.format(
                str(self.comment.author), self.comment.created,
                self.comment.text), str(self.comment))

    def test_models_have_correct_follow_names(self):
        """Проверка заполнения str group"""
        self.assertEqual(
            TEXT_FOLLOW.format(
                str(self.follow.user), str(self.follow.author)),
            str(self.follow))
