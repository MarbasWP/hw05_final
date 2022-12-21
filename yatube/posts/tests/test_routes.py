from django.test import TestCase
from django.urls import reverse

from ..urls import app_name

POST_ID = 1
USERNAME = 'leo'
SLUG = 'Yandex'

ROUTES = (
    ('/', 'index', None),
    (f'/group/{SLUG}/', 'group_list', [SLUG]),
    (f'/profile/{USERNAME}/', 'profile', [USERNAME]),
    (f'/posts/{POST_ID}/', 'post_detail', [POST_ID]),
    ('/create/', 'post_create', None),
    (f'/posts/{POST_ID}/edit/', 'post_edit', [POST_ID]),
    ('/follow/', 'follow_index', None),
    (f'/profile/{USERNAME}/follow/', 'profile_follow', [USERNAME]),
    (f'/profile/{USERNAME}/unfollow/', 'profile_unfollow', [USERNAME]),
    (f'/posts/{POST_ID}/comment/', 'add_comment', [POST_ID])
)


class PostUrlTests(TestCase):
    def test_urls_uses_correct_route(self):
        for url, name, args in ROUTES:
            with self.subTest(url=url):
                self.assertEqual(url, reverse(f'{app_name}:{name}', args=args))
