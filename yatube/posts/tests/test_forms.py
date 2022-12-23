import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django import forms
from django.urls import reverse
from django.conf import settings

from ..models import Post, Group, User, Comment

SLUG = 'Yandex'
USERNAME = 'leo'
INDEX_URL = reverse('posts:index')
CREATE_URL = reverse('posts:post_create')
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
GROUP_LIST_URL = reverse('posts:group_list', args=[SLUG])
LOGIN_URL = f'{reverse("users:login")}?next='
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    """Создаем тестовые посты, группу и форму."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.author2 = Client()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.user2 = User.objects.create_user(username='auth2')
        cls.authorized_client.force_login(cls.user)
        cls.author2.force_login(cls.user2)
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
        cls.another_uploaded = SimpleUploadedFile(
            name='another_small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='New post',
            group=cls.group,
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
            'image': self.image,
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
        self.assertEqual(
            post.image.name,
            f'{Post._meta.get_field("image").upload_to}{form_data["image"]}')

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        form_data = {
            'text': 'Edit post',
            'group': self.group2.id,
            'image': self.another_uploaded,
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
        self.assertEqual(
            post.image.name,
            f'{Post._meta.get_field("image").upload_to}{form_data["image"]}')

    def test_post_edit_page_show_correct_context(self):
        """Шаблон create_post(edit) сформирован с правильным контекстом."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for url in (self.EDIT_URL, CREATE_URL):
            response = self.authorized_client.get(url)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_comment_show_up(self):
        """Комментарий появляется на странице поста"""
        before_creating = set(Comment.objects.all())
        form_data = {
            'text': 'Комментарий',
        }
        response = self.authorized_client.post(
            self.ADD_COMMENT_URL,
            data=form_data,
            follow=True
        )
        after_creating = set(Comment.objects.all())
        differences_of_sets = after_creating.difference(before_creating)
        self.assertEqual(len(differences_of_sets), 1)
        comment = differences_of_sets.pop()
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post, self.post)
        self.assertRedirects(response, self.DETAIL_URL)

    def test_add_comment_guest_client(self):
        """Комментарий не появляется на странице поста
        (неавторизованным пользователем)."""
        before_creating = set(Comment.objects.all())
        form_data = {
            'text': 'Комментарий',
        }
        self.guest_client.post(
            self.ADD_COMMENT_URL,
            data=form_data,
            follow=True)
        self.assertNotIn(
            form_data['text'],
            self.guest_client.get(self.DETAIL_URL).content.decode())
        self.assertEqual(set(Comment.objects.all()), before_creating)

    def test_edit_post_form(self):
        form_data = {
            'text': 'testing',
            'group': self.group2.id,
            'image': self.another_uploaded,
        }
        objects = {
            (self.author2, f'{LOGIN_URL}{self.EDIT_URL}'),
            (self.guest_client, f'{LOGIN_URL}{self.EDIT_URL}')
        }
        for client, expected_redirect in objects:
            with self.subTest(client=client):
                response = self.client.post(self.EDIT_URL,
                                            data=form_data, follow=True)
                post = Post.objects.get(id=self.post.id)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.group.id, self.post.group.id)
                self.assertEqual(post.image.name, self.post.image.name)
                self.assertRedirects(response, expected_redirect)

    def test_guest_create_post_form(self):
        form_data = {
            'text': 'Текст для нового поста',
            'group': self.group.id,
            'image': self.image
        }
        before_creating = set(Post.objects.all())
        response = self.guest_client.post(CREATE_URL,
                                          data=form_data, follow=True)
        after_creating = set(Post.objects.all())
        self.assertEqual(before_creating, after_creating)
        self.assertRedirects(response, f'{LOGIN_URL}{CREATE_URL}')
