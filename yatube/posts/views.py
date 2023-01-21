from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .page import paginator


@cache_page(20)
def index(request):
    posts = Post.objects.select_related('author', 'group')
    return render(request, 'posts/index.html',
                  {'page_obj': paginator(posts, request)})


def group_list(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author')
    return render(request, 'posts/group_list.html',
                  {'group': group, 'page_obj': paginator(posts, request)})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    author_posts = author.posts.select_related('group')
    return render(request, 'posts/profile.html', {
        'author': author,
        'page_obj': paginator(author_posts, request),
        'following': (
            request.user != author
            and request.user.is_authenticated
            and Follow.objects.filter(
                author=author,
                user=request.user
            ).exists())
    })


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.select_related('author')
    return render(request, 'posts/post_detail.html', {
        'post': post,
        'comments': comments,
        'form': CommentForm(request.POST or None),
    })


@login_required()
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', post.author.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id)


@login_required
def follow_index(request):
    posts = Post.objects.select_related('author', 'group').filter(
        author__following__user=request.user)
    context = {
        'page_obj': paginator(posts, request),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    get_object_or_404(
        Follow, user=request.user, author__username=username).delete()
    return redirect('posts:profile', username=username)
