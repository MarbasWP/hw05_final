from django.test import TestCase, Client
from django.urls import reverse
from django import forms

from ..models import Post, Group, User, Comment

FORM_FIELDS = {
    'text': forms.fields.CharField,
    'group': forms.fields.ChoiceField
}
SLUG = 'Yandex'
USERNAME = 'leo'
INDEX_URL = reverse('posts:index')
CREATE_URL = reverse('posts:post_create')
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
GROUP_LIST_URL = reverse('posts:group_list', args=[SLUG])


class PostFormTests(TestCase):
    """Создаем тестовые посты, группу и форму."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.user2 = User.objects.create_user(username='auth2')
        cls.group = Group.objects.create(
            title='YandexPracticum',
            slug=SLUG,
            description='informathion'
        )
        cls.group2 = Group.objects.create(
            title='New Group2',
            slug='Test_Group2'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='New post',
            group=cls.group,
            image=None,
        )
        cls.EDIT_URL = reverse('posts:post_edit', args=(cls.post.id,))
        cls.DETAIL_URL = reverse('posts:post_detail', args=(cls.post.id,))
        cls.ADD_COMMENT_URL = reverse('posts:add_comment', args=(cls.post.id,))

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts = set(Post.objects.all())

        form_data = {
            'text': 'New text',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            CREATE_URL,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, PROFILE_URL)
        set_posts = set(Post.objects.all()) - posts
        self.assertEqual(len(set_posts), 1)
        post = set_posts.pop()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, self.user)

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        form_data = {
            'text': 'Edit post',
            'group': self.group2.id,
        }
        response = self.authorized_client.post(
            self.EDIT_URL,
            data=form_data,
            follow=True
        )
        post = Post.objects.get(pk=self.post.pk)
        self.assertRedirects(response, self.DETAIL_URL)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.pk, form_data['group'])
        self.assertEqual(post.author, self.post.author)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон create_post(edit) сформирован с правильным контекстом."""
        for url in (self.EDIT_URL, CREATE_URL):
            response = self.authorized_client.get(url)
            for value, expected in FORM_FIELDS.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_comment_can_authorized_user(self):
        """Комментировать может только авторизованный пользователь."""
        form_data = {
            'text': 'New text',
        }
        self.assertRedirects(self.authorized_client.post(
            self.ADD_COMMENT_URL,
            data=form_data,
            follow=True),
            self.DETAIL_URL)

    def test_comment_show_up(self):
        """Комментарий появляется на странице поста"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'New text',
        }
        response = self.authorized_client.post(
            self.ADD_COMMENT_URL,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.DETAIL_URL)
        self.assertEqual(Comment.objects.count(), comments_count + 1)
