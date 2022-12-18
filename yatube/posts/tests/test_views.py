from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.conf import settings

from ..models import Group, Post, User, Follow

USERNAME = 'leo'
USERNAME2 = 'auth2'
SLUG1 = 'Yandex'
SLUG2 = 'Test_Group2'
INDEX_URL = reverse('posts:index')
CREATE_URL = reverse('posts:post_create')
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
GROUP_LIST_URL = reverse('posts:group_list', args=[SLUG1])
GROUP_LIST_URL2 = reverse('posts:group_list', args=[SLUG2])
PROFILE_FOLLOW_URL = reverse('posts:profile_follow', args=[USERNAME2])
PROFILE_UNFOLLOW_URL = reverse('posts:profile_unfollow', args=[USERNAME2])
FOLLOW_INDEX_URL = reverse('posts:follow_index')
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


class ViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.user2 = User.objects.create_user(username=USERNAME2)
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.author2 = Client()
        cls.author2.force_login(cls.user2)
        cls.group = Group.objects.create(
            title='YandexPracticum',
            slug=SLUG1,
            description='informathion'
        )
        cls.group2 = Group.objects.create(
            title='New Group2',
            slug=SLUG2
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='New post',
            group=cls.group,
            image=cls.image,
        )
        cls.follow = Follow.objects.get_or_create(
            user=cls.user2,
            author=cls.user
        )

        cls.EDIT_URL = reverse('posts:post_edit', args=(cls.post.id,))
        cls.DETAIL_URL = reverse('posts:post_detail', args=(cls.post.id,))

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
            (self.DETAIL_URL, 'post'),
            (FOLLOW_INDEX_URL, 'page_obj')
        )
        for url, context in URLS:
            with self.subTest(url=url):
                response = self.author2.get(url)
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
            (FOLLOW_INDEX_URL, settings.FIRST_OF_POSTS),
            (f'{FOLLOW_INDEX_URL}?page=2', 2),
        )
        for url, count_posts in PAGES:
            with self.subTest(url=url):
                self.assertEqual(len(self.author2.get(
                    url).context['page_obj']), count_posts)

    def test_cache(self):
        """Проверка работы кеша для главной страницы."""
        post = Post.objects.create(author=self.user, text='какой-то текст')
        posts = (self.authorized_client.get(INDEX_URL)).content
        post.delete()
        posts_cache = (self.authorized_client.get(INDEX_URL)).content
        cache.clear()
        posts_updated = (
            self.authorized_client.get(INDEX_URL)).content
        self.assertEqual(posts, posts_cache)
        self.assertNotEqual(posts_cache, posts_updated)

    def test_users_can_follow_and_unfollow(self):
        """Зарегистрированный пользователь может подписаться и отписаться."""
        follower_count = Follow.objects.count()
        self.authorized_client.post(PROFILE_FOLLOW_URL)
        self.assertEqual(Follow.objects.count(), follower_count + 1)
        self.assertTrue(
            Follow.objects.filter(user=self.user2, author=self.user).exists())
        self.authorized_client.post(PROFILE_UNFOLLOW_URL)
        self.assertEqual(Follow.objects.count(), follower_count)
