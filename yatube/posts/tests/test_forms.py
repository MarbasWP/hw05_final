from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse
from django import forms

from ..forms import CommentForm
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
LOGIN_URL = f'{reverse("users:login")}?next='
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


class PostFormTests(TestCase):
    """Создаем тестовые посты, группу и форму."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.user2 = User.objects.create_user(username='auth2')
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='YandexPracticum',
            slug=SLUG,
            description='informathion'
        )
        cls.group2 = Group.objects.create(
            title='New Group2',
            slug='Test_Group2'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.image_edit = SimpleUploadedFile(
            name='edit.gif',
            content=SMALL_GIF,
            content_type='image/gif',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='New post',
            group=cls.group,
            image=cls.image,
        )
        cls.EDIT_URL = reverse('posts:post_edit', args=(cls.post.id,))
        cls.DETAIL_URL = reverse('posts:post_detail', args=(cls.post.id,))
        cls.ADD_COMMENT_URL = reverse('posts:add_comment', args=(cls.post.id,))

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts = set(Post.objects.all())

        form_data = {
            'text': 'New text',
            'group': self.group.id,
            'image': self.post.image,
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
            'image': self.image_edit,
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

    def test_comment_show_up(self):
        """Комментарий появляется на странице поста"""
        form_data = {
            'author': self.user,
            'post': self.post,
            'text': 'Комментарий',
        }
        response1 = self.authorized_client.post(
            self.ADD_COMMENT_URL,
            data=form_data,
            follow=True
        )
        response_post_detail1 = self.authorized_client.get(self.DETAIL_URL)
        self.assertIsInstance(response1.context['form'], CommentForm)
        self.assertIn(form_data['text'], response_post_detail1.content.decode())

    def test_add_comment_guest_client(self):
        """Комментарий не появляется на странице поста
        (неавторизованным пользователем)."""
        form_data = {
            'author': self.user,
            'post': self.post,
            'text': 'Комментарий',
        }
        self.guest_client.post(
            self.ADD_COMMENT_URL,
            data=form_data,
            follow=True)
        self.assertFalse(Comment.objects.filter(id=self.post.id).exists())
        self.assertNotIn(
            form_data['text'],
            self.guest_client.get(self.DETAIL_URL).content.decode())

    def test_create_and_edit_post_guest_client(self):
        """Запись поста не создаётся и не редактируется
        для неавторизованного пользователя."""
        posts_count = Post.objects.count()
        edit_image = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        objects = {
            CREATE_URL: f'{LOGIN_URL}{CREATE_URL}',
            self.EDIT_URL: f'{LOGIN_URL}{self.EDIT_URL}',
        }
        for reverse_name, redirect_url in objects.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.post(
                    reverse_name,
                    data={'text': 'testing', 'image': edit_image},
                    follow=True
                )
                self.assertRedirects(response, redirect_url)
                self.assertEqual(Post.objects.count(), posts_count)
