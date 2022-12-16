from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse

from ..models import Post, Group, User

USERNAME = 'leo'
SLUG = 'Yandex'
INDEX_URL = reverse('posts:index')
CREATE_URL = reverse('posts:post_create')
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
GROUP_LIST_URL = reverse('posts:group_list', args=[SLUG])
LOGIN_URL = f'{reverse("users:login")}?next='


class PostURLTests(TestCase):
    """Создаем тестовый пост и группу."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.user2 = User.objects.create_user(username='auth2')
        cls.group = Group.objects.create(
            title='YandexPracticum',
            slug='Yandex',
            description='informathion'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='New post'
        )

        cls.EDIT_URL = reverse('posts:post_edit', args=(cls.post.id,))
        cls.DETAIL_URL = reverse('posts:post_detail', args=(cls.post.id,))

    def setUp(self):
        """Создаем клиент гостя и зарегистрированного пользователя."""
        self.guest = Client()
        self.author = Client()
        self.author2 = Client()
        self.author.force_login(self.user)
        self.author2.force_login(self.user2)

    def test_urls_redirect_response_guest(self):
        URLS = (
            (CREATE_URL, self.client,
             f'{LOGIN_URL}{CREATE_URL}'),
            (self.EDIT_URL, self.client,
             f'{LOGIN_URL}{self.EDIT_URL}'),
            (self.EDIT_URL, self.author2, self.DETAIL_URL)
        )
        for url, client, result_url in URLS:
            with self.subTest(url=url, result_url=result_url):
                self.assertRedirects(client.get(
                    url), result_url, HTTPStatus.FOUND)

    def test_urls_response(self):
        URLS = (
            (INDEX_URL, self.guest, HTTPStatus.OK),
            (PROFILE_URL, self.guest, HTTPStatus.OK),
            (GROUP_LIST_URL, self.guest, HTTPStatus.OK),
            (self.DETAIL_URL, self.guest, HTTPStatus.OK),
            (CREATE_URL, self.author, HTTPStatus.OK),
            (self.EDIT_URL, self.author, HTTPStatus.OK),
            ('/test-no-popular', self.guest, HTTPStatus.NOT_FOUND),
            (self.EDIT_URL, self.author2, HTTPStatus.FOUND),
            (CREATE_URL, self.client, HTTPStatus.FOUND),
            (self.EDIT_URL, self.client, HTTPStatus.FOUND)
        )
        for url, client, status in URLS:
            with self.subTest(url=url, status=status):
                self.assertEqual(client.get(url).status_code, status)

    def test_urls_uses_correct_template(self):
        """Проверяем запрашиваемые шаблоны страниц через имена."""
        templates_pages_names = {
            INDEX_URL: 'posts/index.html',
            GROUP_LIST_URL: 'posts/group_list.html',
            PROFILE_URL: 'posts/profile.html',
            self.DETAIL_URL: 'posts/post_detail.html',
            CREATE_URL: 'posts/create_post.html',
            self.EDIT_URL: 'posts/create_post.html',
            '/test-no-popular': 'core/404.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertTemplateUsed(
                    self.author.get(reverse_name),
                    template
                )
