import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
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
        cls.bytes_image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=cls.bytes_image,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись',
            group=cls.group,
            image=cls.image
        )
        cls.post_quantity = Post.objects.count()
        cls.urls = (
            ('posts:index', None, 'posts/index.html'),
            ('posts:profile', (cls.user,), 'posts/profile.html'),
            ('posts:group_list', (cls.group.slug,), 'posts/group_list.html'),
            ('posts:post_detail', (cls.post.id,), 'posts/post_detail.html'),
            ('posts:post_create', None, 'posts/create_post.html'),
            ('posts:post_edit', (cls.post.id,), 'posts/create_post.html'),
            ('posts:follow_index', None, 'posts/follow.html'),
        )
        cls.reverse_profile = reverse('posts:profile', args=(cls.user,))
        cls.reverse_profile_follow = reverse(
            'posts:profile_follow', args=(cls.user,))
        cls.reverse_profile_unfollow = reverse(
            'posts:profile_unfollow', args=(cls.user,))

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_no_author = Client()
        self.authorized_client_no_author.force_login(self.user_no_author)
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
        self.assertEqual(post.image, f'posts/{self.image}')

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
                response = self.authorized_client.get(reverse_page)
                self.check_context(response)
                self.assertContains(response, '<img', count=2)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', args=(self.post.id,))
        )
        self.check_context(response, True)
        self.assertContains(response, '<img', count=2)

    def test_users_can_follow_and_unfollow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок."""
        follower_quantity = Follow.objects.count()
        response = self.authorized_client_no_author.get(
            self.reverse_profile_follow
        )
        self.assertRedirects(
            response, self.reverse_profile,
            HTTPStatus.FOUND
        )
        self.assertEqual(Follow.objects.count(), follower_quantity + 1)
        response = self.authorized_client_no_author.get(
            self.reverse_profile_unfollow
        )
        self.assertRedirects(
            response, self.reverse_profile,
            HTTPStatus.FOUND
        )
        self.assertEqual(Follow.objects.count(), follower_quantity)

    def test_post_appears_at_feed(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется - кто не подписан."""
        Follow.objects.get_or_create(
            user=self.user_no_author,
            author=self.user
        )
        response = self.authorized_client_no_author.get(
            reverse('posts:follow_index')
        )
        self.assertContains(response, self.post)
        Follow.objects.filter(
            user=self.user_no_author,
            author__username=self.user.username
        ).delete()
        response = self.authorized_client_no_author.get(
            reverse('posts:follow_index')
        )
        self.assertNotContains(response, self.post)

    def test_cache_from_index_page(self):
        """Кэширование работает."""
        reverse_index = reverse("posts:index")
        page_content = self.authorized_client.get(reverse_index).content
        Post.objects.all().delete()
        self.assertEqual(page_content,
                         self.authorized_client.get(reverse_index).content)
        cache.clear()
        self.assertNotEqual(page_content,
                            self.authorized_client.get(reverse_index).content)
