from django.core.paginator import Paginator

from posts.models import Follow


def get_page(request, object_list, per_page=10):
    page_number = request.GET.get('page')
    paginator = Paginator(object_list, per_page)
    page = paginator.get_page(page_number)
    return page


def is_follow(user, author_username):
    return Follow.objects.filter(
        user__username=user,
        author__username=author_username,
    ).exists()
