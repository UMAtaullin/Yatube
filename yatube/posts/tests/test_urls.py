from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Author')
        cls.user_no_author = User.objects.create_user(username='NoAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись',
            group=cls.group,
        )
        cls.urls = (
            ('posts:index', None, 'posts/index.html', '/'),
            ('posts:profile', (cls.user,), 'posts/profile.html',
             f'/profile/{cls.user.username}/'),
            ('posts:group_list', (cls.group.slug,), 'posts/group_list.html',
             f'/group/{cls.group.slug}/'),
            ('posts:post_detail', (cls.post.id,), 'posts/post_detail.html',
             f'/posts/{cls.post.id}/'),
            ('posts:post_create', None, 'posts/create_post.html', '/create/'),
            ('posts:post_edit', (cls.post.id,), 'posts/create_post.html',
             f'/posts/{cls.post.id}/edit/'),
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_no_author = Client()
        self.authorized_client_no_author.force_login(self.user_no_author)
        cache.clear()

    def test_reverse(self):
        """Проверка реверсов."""
        for url, args, _, hard_link in self.urls:
            reverse_name = reverse(url, args=args)
            with self.subTest(reverse_name=hard_link):
                self.assertEqual(reverse_name, hard_link)

    def test_404_nonexistent_page(self):
        """Проверка 404 для несуществующих страниц."""
        url = '/unexisting_page/'
        roles = (
            self.authorized_client,
            self.authorized_client_no_author,
            self.client,
        )
        for role in roles:
            with self.subTest(url=url):
                response = role.get(url, follow=True)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
                self.assertTemplateUsed(response, 'core/404.html')
