from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Group, Post, User


class PostFormTests(TestCase):
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
        cls.form = PostForm()
        cls.post_quantity = Post.objects.count()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_no_author = Client()
        self.authorized_client_no_author.force_login(self.user_no_author)

    def test_edit_form_only_for_author(self):
        """Запись может редактировать только автор + перенаправление."""
        roles = (
            self.authorized_client_no_author,
            self.client,
        )
        for role in roles:
            with self.subTest(role=role):
                reverse_name = reverse('posts:post_edit', args=(self.post.id,))
                response = role.post(reverse_name)
                if role == self.authorized_client_no_author:
                    self.assertRedirects(response, reverse(
                        'posts:post_detail', args=(self.post.id,)),
                        HTTPStatus.FOUND
                    )
                else:
                    login = reverse(settings.LOGIN_URL)
                    self.assertRedirects(
                        response,
                        f'{login}?{REDIRECT_FIELD_NAME}={reverse_name}',
                        HTTPStatus.FOUND
                    )
        self.assertEqual(self.post_quantity, self.post_quantity)

    def test_guest_cant_create_post(self):
        """Гость не может создавать записи."""
        reverse_name = reverse('posts:post_create')
        response = self.client.post(reverse_name)
        login = reverse(settings.LOGIN_URL)
        self.assertRedirects(
            response,
            f'{login}?{REDIRECT_FIELD_NAME}={reverse_name}',
            HTTPStatus.FOUND
        )

    def test_comment_for_registered_users(self):
        """Комментарии могут оставлять авторизованные пользователи."""
        roles = (
            self.authorized_client.post,
            self.authorized_client_no_author.post,
        )
        for role in roles:
            with self.subTest(role=role):
                comment_data = {
                    'text': 'тестовый коммент',
                }
                response = role(
                    reverse('posts:add_comment', args=(self.post.id,)),
                    data=comment_data,
                    follow=True,
                )
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertRedirects(response, reverse(
                    'posts:post_detail', args=(self.post.id,)),
                    HTTPStatus.FOUND
                )
                comment = Comment.objects.first()
                self.assertEqual(comment.text, comment.text)
        self.assertEqual(Comment.objects.count(), 2)

    def test_comment_cant_comment(self):
        """Комментарии не могут оставлять гости."""
        comment_data = {
            'text': 'тестовый коммент',
        }
        reverse_name = reverse('posts:add_comment', args=(self.post.id,))
        response = self.client.post(
            reverse_name,
            data=comment_data,
            follow=True,
        )
        login = reverse(settings.LOGIN_URL)
        self.assertRedirects(
            response,
            f'{login}?{REDIRECT_FIELD_NAME}={reverse_name}',
            HTTPStatus.FOUND
        )
        self.assertEqual(Comment.objects.count(), 0)
