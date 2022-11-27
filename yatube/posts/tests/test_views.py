from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from django.core.cache import cache

from posts.models import Group, Post, Follow
from posts.constans import POST_LIMIT

User = get_user_model()


class PostPagesTests(TestCase):
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
        self.post_author.force_login(self.user_author)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_posts', kwargs={'slug': 'test-slug'}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'author'}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
            'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
            'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_group_post_profile_page_show_correct_context(self):
        """Шаблон главной страницы, group_post, profile
         сформирован с правильным контекстом.
        """
        context_response = [
            self.authorized_client.get(reverse('posts:index')),
            self.authorized_client.get(reverse(
                'posts:group_posts', kwargs={'slug': self.group.slug})),
            self.authorized_client.get(reverse(
                'posts:profile',
                kwargs={'username': self.post.author.username})),
        ]
        for response in context_response:
            first_object = response.context['page_obj'][0]
            context_objects = {
                self.post.author: first_object.author,
                self.post.text: first_object.text,
                self.group.slug: first_object.group.slug,
                self.post.id: first_object.id,
                self.post.image: first_object.image,
            }
            for reverse_name, response_name in context_objects.items():
                with self.subTest(reverse_name=reverse_name):
                    self.assertEqual(response_name, reverse_name)

    def test_profile_page_show_correct_context_author(self):
        """Шаблон страницы profile
        сформирован с правильным контекстом по 'author'."""
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.post.author.username})).context['author']
        self.assertEqual(response, self.author)

    def test_profile_page_show_correct_context_following(self):
        """Шаблон страницы profile
        сформирован с правильным контекстом по 'following'."""
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.post.author.username}
        )).context['following']
        self.assertIsInstance(response, bool, msg=None)
        self.assertEqual(response, False)

    def test_group_post_page_show_correct_context(self):
        """Шаблон страницы group_post
         сформирован с правильным контекстом 'group'.
        """
        first_object = self.authorized_client.get(reverse(
            'posts:group_posts',
            kwargs={'slug': self.group.slug})).context['group']
        context_objects = {
            self.group.title: first_object.title,
            self.group.description: first_object.description,
            self.group.slug: first_object.slug,
            self.group.id: first_object.id,
        }
        for reverse_name, response_name in context_objects.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertEqual(response_name, reverse_name)

    def test_post_detail_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        first_object = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id},)).context['post']
        context_objects = {
            self.post.author: first_object.author,
            self.post.text: first_object.text,
            self.post.group: first_object.group,
            self.post.id: first_object.id,
            self.post.image: first_object.image,
        }
        for reverse_name, response_name in context_objects.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertEqual(response_name, reverse_name)

    def test_post_create_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        self.assertEqual(response.context['post'].author.username,
                         self.author.username)
        self.assertEqual(response.context['post'].text,
                         self.post.text)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertIsInstance(response.context['is_edit'], bool, msg=None)
        self.assertEqual(response.context['is_edit'], True)

    def test_index_cache_context(self):
        """Тест кеширования главной страницы"""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 1)
        post = Post.objects.create(
            author=self.author,
            group=self.group,
            text='Текст поста для кеш',
        )
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 2)
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 2)
        post.delete()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 1)
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 1)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.POST_SECOND_PAGE = 3
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        for num_post in range(POST_LIMIT + cls.POST_SECOND_PAGE):
            cls.post = Post.objects.create(
                author=cls.user,
                group=cls.group,
                text=f'{num_post}Тестовый пост',
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_first_page_contains_ten_records(self):
        templates = [
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.post.author.username})
        ]
        for template in templates:
            with self.subTest(template=template):
                response = self.client.get(template)
                self.assertEqual(len(response.context['page_obj']), POST_LIMIT)

    def test_second_page_contains_three_records(self):
        templates = [
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.post.author.username})
        ]
        for template in templates:
            with self.subTest(template=template):
                response = self.client.get(template + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']), self.POST_SECOND_PAGE)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.users = User.objects.create_user(username='user')
        cls.authors = User.objects.create_user(username='author')
        cls.post_author = Post.objects.create(
            text='Привет',
            author=cls.authors,
        )
        cls.post_user = Post.objects.create(
            text='Тест',
            author=cls.users,
        )

    def setUp(self):
        cache.clear()
        self.user = Client()
        self.author = Client()
        self.user.force_login(self.users)
        self.author.force_login(self.authors)

    def test_authorizent_client_follow(self):
        """Проверка авторизованного пользователя подписаться."""
        follow_count = Follow.objects.count()
        self.user.get(
            reverse(('posts:profile_follow'),
                    kwargs={'username': f'{self.authors.username}'}))
        self.assertEqual(Follow.objects.count(), follow_count + 1)

    def test_authorizent_client_unfollow(self):
        """Проверка авторизованного пользователя отписаться."""
        Follow.objects.create(user=self.users, author=self.authors)
        follow_count = Follow.objects.count()
        self.user.get(
            reverse(('posts:profile_unfollow'),
                    kwargs={'username': f'{self.authors.username}'}))
        self.assertEqual(Follow.objects.count(), follow_count - 1)

    def test_folow_on_self(self):
        """Проверка подписки на себя."""
        follow_count = Follow.objects.count()
        self.user.get(
            reverse(('posts:profile_follow'),
                    kwargs={'username': f'{self.users.username}'}))
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_posts_follow(self):
        """Проверка постов на странице подписки."""
        self.user.get(
            reverse(('posts:profile_follow'),
                    kwargs={'username': f'{self.authors.username}'}))
        response = self.user.get(reverse('posts:follow_index'))
        self.assertEqual(
            len(response.context['page_obj']),
            Post.objects.filter(author=self.authors).count()
        )
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_posts_unfollow(self):
        "Проверка постов после отписки."
        self.user.get(
            reverse(('posts:profile_unfollow'),
                    kwargs={'username': f'{self.authors.username}'}))
        response = self.user.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)
