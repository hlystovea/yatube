from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from posts.forms import CommentForm, PostForm
from posts.models import Comment, Group, Post

User = get_user_model()


@cache_page(20, key_prefix="index_page")
def index(request):
    post_list = Post.objects.select_related('group')

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    context = {
        'page': page,
        'paginator': paginator,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    context = {
        'group': group,
        'page': page,
        'paginator': paginator,
    }
    return render(request, 'group.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    context = {
        'author': author,
        'page': page,
        'paginator': paginator,
    }
    return render(request, 'posts/profile.html', context)


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    comments = post.comments.all()

    paginator = Paginator(comments, 3)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'post': post,
        'author': post.author,
        'page': page,
        'paginator': paginator,
    }
    return render(request, 'posts/post.html', context)


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        form.instance.author = request.user
        form.save()
        return redirect('posts:index')
    context = {
        'form': form,
        'is_edit': False,
    }
    return render(request, 'posts/post_form.html', context)


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    if post.author == request.user:
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=post
        )
        if form.is_valid():
            form.save()
            return redirect('posts:post', username=username, post_id=post_id)
        context = {
            'post': post,
            'form': form,
            'is_edit': True,
        }
        return render(request, 'posts/post_form.html', context)
    return redirect('posts:post', username=username, post_id=post_id)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    comments = post.comments.all()

    paginator = Paginator(comments, 3)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    form = CommentForm(request.POST or None)
    if form.is_valid():
        form.instance.author = request.user
        form.instance.post = post
        form.save()
        return redirect('posts:post', username=username, post_id=post_id)
    context = {
        'form': form,
        'post': post,
        'page': page,
        'paginator': paginator,
    }
    return render(request, 'posts/post.html', context)


@login_required
def edit_comment(request, username, post_id, comment_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    comments = Comment.objects.filter(post=post)
    comment = get_object_or_404(comments, id=comment_id)

    paginator = Paginator(comments, 3)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    if comment.author == request.user:
        form = CommentForm(
            request.POST or None,
            instance=comment
        )
        if form.is_valid():
            form.save()
            return redirect('posts:post', username=username, post_id=post_id)
        context = {
            'form': form,
            'post': post,
            'comment': comment,
            'page': page,
            'paginator': paginator,
        }
        return render(request, 'posts/post.html', context)
    return redirect('posts:post', username=username, post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.prefetch_related()
    context = {
        "page": page
    }
    return render(request, "follow.html", context)


@login_required
def profile_follow(request, username):
    # ...
    pass


@login_required
def profile_unfollow(request, username):
    # ...
    pass 


def page_not_found(request, exception):
    return render(request, 'misc/404.html', {'path': request.path}, status=404)


def server_error(request):
    return render(request, 'misc/500.html', status=500)
