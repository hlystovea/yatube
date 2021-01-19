from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from posts.forms import CommentForm, PostForm
from posts.models import Comment, Follow, Group, Post
from posts.utils import get_page, is_follow

User = get_user_model()


def index(request):
    post_list = Post.objects.select_related('group', 'author')
    page = get_page(request, post_list)
    context = {
        'page': page,
        'paginator': page.paginator,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(
        Group.objects.prefetch_related('posts'),
        slug=slug,
    )
    post_list = group.posts.select_related('author')
    page = get_page(request, post_list)
    context = {
        'group': group,
        'page': page,
        'paginator': page.paginator,
    }
    return render(request, 'posts/group.html', context)


def profile(request, username):
    author = get_object_or_404(
        User.objects.prefetch_related('posts'),
        username=username,
    )
    post_list = author.posts.prefetch_related('comments')
    page = get_page(request, post_list)
    context = {
        'author': author,
        'page': page,
        'paginator': page.paginator,
        'is_follow': is_follow(request.user, username),
    }
    return render(request, 'posts/profile.html', context)


def post_view(request, username, post_id):
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'),
        id=post_id,
        author__username=username,
    )
    comments = post.comments.select_related('author')
    context = {
        'post': post,
        'comments': comments,
        'is_follow': is_follow(request.user, username),
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
    post = get_object_or_404(
        Post.objects.select_related('author'),
        id=post_id,
        author__username=username,
    )
    if request.user == post.author:
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=post,
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


@require_POST
@login_required
def post_del(request, username, post_id):
    post = get_object_or_404(
        Post.objects.select_related('author'),
        author__username=username,
        id=post_id,
    )
    if request.user == post.author:
        post.delete()
    return redirect(
        request.META.get('HTTP_REFERER', 'posts:profile'),
        username=username,
    )


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'),
        id=post_id,
        author__username=username,
    )
    comments = post.comments.select_related('author')
    form = CommentForm(request.POST or None)
    if form.is_valid():
        form.instance.author = request.user
        form.instance.post = post
        form.save()
        return redirect('posts:post', username=username, post_id=post_id)
    context = {
        'form': form,
        'post': post,
        'author': post.author,
        'comments': comments,
        'is_follow': is_follow(request.user, username),
    }
    return render(request, 'posts/post.html', context)


@login_required
def comment_edit(request, username, post_id, comment_id):
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'),
        id=post_id,
        author__username=username,
    )
    comments = post.comments.select_related('author')
    comment = get_object_or_404(comments, post=post, id=comment_id)

    if request.user == comment.author:
        form = CommentForm(
            request.POST or None,
            instance=comment,
        )
        if form.is_valid():
            form.save()
            return redirect('posts:post', username=username, post_id=post_id)
        context = {
            'form': form,
            'post': post,
            'comment_id': comment_id,
            'comments': comments,
            'is_follow': is_follow(request.user, username),
        }
        return render(request, 'posts/post.html', context)
    return redirect('posts:post', username=username, post_id=post_id)


@require_POST
@login_required
def comment_del(request, username, post_id, comment_id):
    comment = get_object_or_404(
        Comment.objects.select_related('author'),
        post_id=post_id,
        id=comment_id,
    )
    if request.user == comment.author:
        comment.delete()
    return redirect('posts:post', username=username, post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(
        author__following__user=request.user).select_related('author', 'group')
    page = get_page(request, post_list)
    context = {
        'page': page,
        'paginator': page.paginator,
    }
    return render(request, "posts/follow.html", context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if not author == request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect(
        request.META.get('HTTP_REFERER', 'posts:profile'),
        username=username,
    )


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=request.user, author=author)
    follow.delete()
    return redirect(
        request.META.get('HTTP_REFERER', 'posts:profile'),
        username=username,
    )


def page_not_found(request, exception):
    return render(request, 'misc/404.html', {'path': request.path}, status=404)


def server_error(request):
    return render(request, 'misc/500.html', status=500)
