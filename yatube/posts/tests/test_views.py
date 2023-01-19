from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostViewsTests(TestCase):
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
        cls.post_quantity = Post.objects.count()
        cls.urls = (
            ('posts:index', None, 'posts/index.html'),
            ('posts:profile', (cls.user,), 'posts/profile.html'),
            ('posts:group_list', (cls.group.slug,), 'posts/group_list.html'),
            ('posts:post_detail', (cls.post.id,), 'posts/post_detail.html'),
            ('posts:post_create', None, 'posts/create_post.html'),
            ('posts:post_edit', (cls.post.id,), 'posts/create_post.html'),
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_no_author = Client()
        self.authorized_client_no_author.force_login(self.user_no_author)
        self.follower = User.objects.create(
            username='follower'
        )
        self.follower_client = Client()
        cache.clear()

    def test_pages_uses_correct_template(self):
        """View-функции использует соответствующий шаблон."""
        for url, args, template in self.urls:
            reverse_name = reverse(url, args=args)
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def check_context(self, response, bool=False):
        """Функция для передачи контекста."""
        if bool:
            post = response.context.get('post')
        else:
            post = response.context['page_obj'][0]
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.pub_date, self.post.pub_date)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, self.group)

    def test_pages_show_correct_context(self):
        """Шаблоны сформированы с правильным контекстом."""
        context = {reverse('posts:index'): self.post,
                   reverse('posts:profile',
                   kwargs={'username': self.user.username,
                           }): self.post,
                   reverse('posts:group_list',
                   kwargs={'slug': self.group.slug,
                           }): self.post,
                   }
        for reverse_page, object in context.items():
            with self.subTest(reverse_page=reverse_page):
                response = self.follower_client.get(reverse_page)
                self.check_context(response)
