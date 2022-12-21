from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse

from ..models import Post, Group, User, Follow

USERNAME = 'leo'
SLUG = 'Yandex'
INDEX_URL = reverse('posts:index')
CREATE_URL = reverse('posts:post_create')
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
GROUP_LIST_URL = reverse('posts:group_list', args=[SLUG])
LOGIN_URL = f'{reverse("users:login")}?next='
PROFILE_FOLLOW_URL = reverse('posts:profile_follow', args=[USERNAME])
PROFILE_UNFOLLOW_URL = reverse('posts:profile_unfollow', args=[USERNAME])
FOLLOW_INDEX_URL = reverse('posts:follow_index')


class PostURLTests(TestCase):
    """Создаем тестовый пост и группу."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.user2 = User.objects.create_user(username='auth2')
        cls.guest = Client()
        cls.author = Client()
        cls.author2 = Client()
        cls.author.force_login(cls.user)
        cls.author2.force_login(cls.user2)
        cls.group = Group.objects.create(
            title='YandexPracticum',
            slug='Yandex',
            description='informathion'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='New post'
        )
        cls.follow = Follow.objects.create(
            user=cls.user2,
            author=cls.user
        )

        cls.EDIT_URL = reverse('posts:post_edit', args=(cls.post.id,))
        cls.DETAIL_URL = reverse('posts:post_detail', args=(cls.post.id,))

    def test_urls_redirect_response_guest(self):
        URLS = (
            (CREATE_URL, self.client,
             f'{LOGIN_URL}{CREATE_URL}'),
            (self.EDIT_URL, self.client,
             f'{LOGIN_URL}{self.EDIT_URL}'),
            (self.EDIT_URL, self.author2, self.DETAIL_URL),
            (FOLLOW_INDEX_URL, self.client, f'{LOGIN_URL}{FOLLOW_INDEX_URL}'),
            (PROFILE_FOLLOW_URL, self.author2, PROFILE_URL),
            (PROFILE_UNFOLLOW_URL, self.author2, PROFILE_URL),
            (PROFILE_FOLLOW_URL, self.client,
             f'{LOGIN_URL}{PROFILE_FOLLOW_URL}'),
            (PROFILE_UNFOLLOW_URL, self.client,
             f'{LOGIN_URL}{PROFILE_UNFOLLOW_URL}'),
        )
        for url, client, result_url in URLS:
            with self.subTest(url=url, result_url=result_url):
                self.assertRedirects(client.get(
                    url), result_url, HTTPStatus.FOUND)

    def test_urls_response(self):
        URLS = (
            ('/test-no-popular', self.guest, HTTPStatus.NOT_FOUND),
            (CREATE_URL, self.client, HTTPStatus.FOUND),
            (CREATE_URL, self.author, HTTPStatus.OK),
            (FOLLOW_INDEX_URL, self.author2, HTTPStatus.OK),
            (FOLLOW_INDEX_URL, self.guest, HTTPStatus.FOUND),
            (GROUP_LIST_URL, self.guest, HTTPStatus.OK),
            (INDEX_URL, self.guest, HTTPStatus.OK),
            (PROFILE_FOLLOW_URL, self.author2, HTTPStatus.FOUND),
            (PROFILE_UNFOLLOW_URL, self.author2, HTTPStatus.FOUND),
            (PROFILE_FOLLOW_URL, self.guest, HTTPStatus.FOUND),
            (PROFILE_UNFOLLOW_URL, self.guest, HTTPStatus.FOUND),
            (PROFILE_FOLLOW_URL, self.author, HTTPStatus.FOUND),
            (PROFILE_UNFOLLOW_URL, self.author, HTTPStatus.FOUND),
            (PROFILE_URL, self.guest, HTTPStatus.OK),
            (self.DETAIL_URL, self.guest, HTTPStatus.OK),
            (self.EDIT_URL, self.author, HTTPStatus.OK),
            (self.EDIT_URL, self.author2, HTTPStatus.FOUND),
            (self.EDIT_URL, self.client, HTTPStatus.FOUND),
        )
        for url, client, status in URLS:
            with self.subTest(url=url, client=client, status=status):
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
            FOLLOW_INDEX_URL: 'posts/follow.html'
        }
        for url, template in templates_pages_names.items():
            with self.subTest(url=url):
                self.assertTemplateUsed(
                    self.author.get(url),
                    template
                )
