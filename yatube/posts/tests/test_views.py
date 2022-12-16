from http import HTTPStatus

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.conf import settings

from ..models import Group, Post, User, Follow

USERNAME = 'leo'
SLUG1 = 'Yandex'
SLUG2 = 'Test_Group2'
INDEX_URL = reverse('posts:index')
CREATE_URL = reverse('posts:post_create')
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
GROUP_LIST_URL = reverse('posts:group_list', args=[SLUG1])
GROUP_LIST_URL2 = reverse('posts:group_list', args=[SLUG2])
PROFILE_FOLLOW_URL = reverse('posts:profile_follow', args=[USERNAME])
PROFILE_UNFOLLOW_URL = reverse('posts:profile_unfollow', args=[USERNAME])
FOLLOW_INDEX_URL = reverse('posts:follow_index')


class ViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.user2 = User.objects.create_user(username='auth2')
        cls.group = Group.objects.create(
            title='YandexPracticum',
            slug=SLUG1,
            description='informathion'
        )
        cls.group2 = Group.objects.create(
            title='New Group2',
            slug=SLUG2
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='New post',
            group=cls.group,
            image=cls.image
        )

        cls.EDIT_URL = reverse('posts:post_edit', args=(cls.post.id,))
        cls.DETAIL_URL = reverse('posts:post_detail', args=(cls.post.id,))

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author2 = Client()
        self.author2.force_login(self.user2)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        self.assertEqual(self.authorized_client.get(
            PROFILE_URL).context.get('author'), self.user)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        group = self.authorized_client.get(GROUP_LIST_URL).context.get('group')
        self.assertEqual(group, self.group)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.description, self.group.description)

    def test_post_not_appear_in_another_group(self):
        """Пост НЕ появляется в другой группе."""
        self.assertNotIn(
            self.post,
            self.authorized_client.get(GROUP_LIST_URL2).context['page_obj']
        )

    def test_post_created_correctly(self):
        """Пост при создании добавлен корректно"""
        URLS = (
            (INDEX_URL, 'page_obj'),
            (GROUP_LIST_URL, 'page_obj'),
            (PROFILE_URL, 'page_obj'),
            (self.DETAIL_URL, 'post')
        )
        for url, context in URLS:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                if context == 'page_obj':
                    paginator_page = response.context.get(context)
                    self.assertEqual(len(list(paginator_page)), 1)
                    post = paginator_page[0]
                elif context == 'post':
                    post = response.context.get(context)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.id, self.post.id)
                self.assertEqual(post.image, self.post.image)

    def test_correct_page_context_guest_client(self):
        """Проверка количества постов на первой и второй страницах."""
        Post.objects.bulk_create(Post(
            text=f'Тестовый текст {i}',
            group=self.group,
            author=self.user,
            image=self.image)
            for i in range(settings.FIRST_OF_POSTS + 1)
        )
        PAGES = (
            (INDEX_URL, settings.FIRST_OF_POSTS),
            (f'{INDEX_URL}?page=2', 2),
            (GROUP_LIST_URL, settings.FIRST_OF_POSTS),
            (f'{GROUP_LIST_URL}?page=2', 2),
            (PROFILE_URL, settings.FIRST_OF_POSTS),
            (f'{PROFILE_URL}?page=2', 2),
        )
        for url, count_posts in PAGES:
            with self.subTest(url=url):
                self.assertEqual(len(self.guest_client.get(
                    url).context['page_obj']), count_posts)

    def test_cache(self):
        post = Post.objects.create(
            author=self.user,
            text='Text cache',
            group=self.group,
            image=self.image,
        )
        response_1 = self.client.get(INDEX_URL)
        self.assertTrue(Post.objects.get(pk=post.id))
        Post.objects.get(pk=post.id).delete()
        cache.clear()
        response_2 = self.client.get(INDEX_URL)
        self.assertNotEqual(response_1.content, response_2.content)

    def test_users_can_follow_and_unfollow(self):
        """Зарегистрированный пользователь может подписаться и отписаться."""
        follower_count = Follow.objects.count()
        self.assertRedirects(
            self.author2.get(PROFILE_FOLLOW_URL),
            PROFILE_URL,
            HTTPStatus.FOUND
        )
        self.assertEqual(Follow.objects.count(), follower_count + 1)
        self.assertRedirects(
            self.author2.get(PROFILE_UNFOLLOW_URL),
            PROFILE_URL,
            HTTPStatus.FOUND
        )
        self.assertEqual(Follow.objects.count(), follower_count)

    def test_post_appears_at_feed(self):
        """Пост появляется в ленте подписчика."""
        Follow.objects.get_or_create(
            user=self.user2,
            author=self.user
        )
        self.assertContains(self.author2.get(FOLLOW_INDEX_URL), self.post)
        Follow.objects.filter(
            user=self.user2,
            author=self.user
        ).delete()
        self.assertNotContains(self.author2.get(FOLLOW_INDEX_URL), self.post)
