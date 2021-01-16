from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from posts.forms import CommentForm, PostForm
from posts.models import Comment, Follow, Group, Post

User = get_user_model()


def paginator_aux(request, object_list, per_page=10):
    paginator = Paginator(object_list, per_page)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return page, paginator


def follow_aux(request, username):
    return Follow.objects.filter(
        user__username=request.user,
        author__username=username,
    ).exists()


def index(request):
    post_list = Post.objects.select_related('group').all()
    page, paginator = paginator_aux(request, post_list)
    context = {
        'page': page,
        'paginator': paginator,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page, paginator = paginator_aux(request, post_list)
    context = {
        'group': group,
        'page': page,
        'paginator': paginator,
    }
    return render(request, 'group.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    page, paginator = paginator_aux(request, post_list)
    context = {
        'author': author,
        'page': page,
        'paginator': paginator,
        'is_follow': follow_aux(request, username),
    }
    return render(request, 'posts/profile.html', context)


def post_view(request, username, post_id):
    if request.POST:
        add_comment(request, username, post_id)
    post = get_object_or_404(
        Post.objects.prefetch_related('comments'),
        id=post_id,
        author__username=username,
    )
    comments = post.comments.all()
    form = CommentForm()
    context = {
        'form': form,
        'post': post,
        'author': post.author,
        'comments': comments,
        'is_follow': follow_aux(request, username),
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
    if request.user.username == username:
        post = get_object_or_404(Post, id=post_id, author__username=username)
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


@login_required
def post_del(request, username, post_id):
    if request.user.username == username:
        post = get_object_or_404(Post, author__username=username, id=post_id)
        post.delete()
    return redirect(
        request.META.get('HTTP_REFERER', 'posts:profile'),
        username=username,
    )


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(
        Post.objects.prefetch_related('comments'),
        id=post_id,
        author__username=username,
    )
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    if form.is_valid():
        form.instance.author = request.user
        form.instance.post = post
        form.save()
        return redirect('posts:post', username=username, post_id=post_id)
    context = {
        'form': form,
        'post': post,
        'comments': comments,
        'is_follow': follow_aux(request, username),
    }
    return render(request, 'posts/post.html', context)


@login_required
def comment_edit(request, username, post_id, comment_id):
    post = get_object_or_404(
        Post.objects.prefetch_related('comments'),
        id=post_id,
        author__username=username,
    )
    comment = get_object_or_404(Comment, post=post, id=comment_id)
    comments = post.comments.all()

    if comment.author == request.user:
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
            'comment': comment,
            'comments': comments,
            'is_follow': follow_aux(request, username),
        }
        return render(request, 'posts/post.html', context)
    return redirect('posts:post', username=username, post_id=post_id)


@login_required
def comment_del(request, username, post_id, comment_id):
    if request.user.username == username:
        comment = get_object_or_404(
            Comment,
            author__username=username,
            post__id=post_id,
            id=comment_id,
        )
        comment.delete()
    return redirect('posts:post', username=username, post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    page, paginator = paginator_aux(request, post_list)
    context = {
        'page': page,
        'paginator': paginator,
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
