from http import HTTPStatus

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.core.cache import cache

from posts.models import Group, Post


User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='Тестовый пост',
        )

    def setUp(self):
        self.user_author = User.objects.create_user(username='author')
        self.post_author = Client()
        self.post_author.force_login(self.author)
        self.user = User.objects.create_user(username='not_author')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_un_existing_page(self):
        """Страница вернет ошибку 404"""
        response = self.client.get('/unexistint_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_url_exists_at_desired_location(self):
        """Страница доступна любому пользователю."""
        url_list = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user_author}/',
            f'/posts/{self.post.id}/',
        ]
        for addres in url_list:
            with self.subTest(addres=addres):
                response = self.client.get(addres)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_exists_at_desired_location_authorized(self):
        """Страница доступна авторизованному пользователю."""
        url_list = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user}/',
            f'/posts/{self.post.id}/',
            '/create/',
        ]
        for addres in url_list:
            with self.subTest(addres=addres):
                response = self.authorized_client.get(addres)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_page_with_author(self):
        """Страница /posts/<post_id>/edit доступна только автору"""
        response = self.post_author.get(reverse(
            'posts:post_edit', args=(self.post.id,)))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
        }
        for template, address in templates_url_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(template)
                self.assertTemplateUsed(response, address)

    def test_urls_post_edit_used_correct_template(self):
        """URL-адрес редактирования поста
        использует соответствующий шаблон."""
        response = self.post_author.get(f'/posts/{self.post.id}/edit/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_guest_entrance_on_privat_post(self):
        """Проверка  при попытке гостя зайти на приватные страницы."""
        response_redirect_page = {
            reverse('posts:post_create'):
            '/auth/login/?next=/create/',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
            f'/auth/login/?next=/posts/{self.post.id}/edit/',
        }
        for reverse_name, redirect in response_redirect_page.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
                self.assertRedirects(response, redirect)

    def test_authorized_client_edit_post_not_author(self):
        """Проверка при попытке не автора отредактировать пост."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}))
        self.assertRedirects(response, f'/posts/{self.post.id}/')
