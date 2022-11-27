from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.core.cache import cache

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from .utils import paginat


def index(request):
    """Шаблон главной страницы."""
    cache.clear()
    posts = cache.get("posts", None)
    if posts is None:
        posts = list(Post.objects.all())
        page_obj = paginat(request, posts)
    context = {
        'page_obj': page_obj,
    }

    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Выводит шаблон группы постов."""
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.select_related('group')
    page_obj = paginat(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj,
    }

    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Выводит шаблон профиля автора постов."""
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related('author')
    following = (
        request.user.is_authenticated
        and author.following.filter(user=request.user).exists()
    )
    page_obj = paginat(request, posts)
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }

    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Выводит шаблон поста."""
    post = get_object_or_404(Post.objects.select_related(
        'author',
        'group',
    ), id=post_id)
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }

    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Выводит шаблон создания поста."""
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid() and request.method == "POST":
        post = form.save(commit=False)
        post.author = request.user
        form.save()

        return redirect('posts:profile', username=post.author)

    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """Выводит шаблон страницы редактирования поста."""
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:

        return redirect('posts:post_detail', post_id)

    form = PostForm(
        request.POST or None,
        instance=post,
        files=request.FILES or None,
    )
    if form.is_valid() and request.method == "POST":
        form.save()

        return redirect('posts:post_detail', post_id)

    return render(
        request,
        'posts/create_post.html',
        {'form': form, 'is_edit': True, 'post': post},
    )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()

    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = paginat(request, posts)
    context = {
        'page_obj': page_obj,
    }

    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписка."""
    following = get_object_or_404(User, username=username)
    already_follows = Follow.objects.filter(
        user=request.user,
        author=following,
    ).exists()
    if request.user.username == username or already_follows:
        return redirect('posts:profile', username=username)

    Follow.objects.create(user=request.user, author=following)

    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Отписка."""
    following = get_object_or_404(User, username=username)
    Follow.objects.filter(author=following, user=request.user).delete()

    return redirect('posts:profile', username=username)
