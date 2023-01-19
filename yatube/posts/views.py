from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm
from .models import Group, Post, User
from .page import paginator


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
    return render(request, 'posts/profile.html',
                  {'author': author,
                   'page_obj': paginator(author_posts, request)})


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    return render(request, 'posts/post_detail.html', {'post': post})


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
