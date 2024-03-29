from django.urls import path

from posts import views

app_name = 'posts'

urlpatterns = [
    path('', views.index, name='index'),
    path('404', views.page_not_found, name='404'),
    path('500', views.server_error, name='500'),
    path('group/<slug:slug>/', views.group_posts, name='group'),
    path('new/', views.new_post, name='new_post'),
    path('follow/', views.follow_index, name='follow_index'),
    path('<str:username>/follow/', views.profile_follow, name='profile_follow'), # noqa
    path('<str:username>/unfollow/', views.profile_unfollow, name='profile_unfollow'), # noqa
    path('<str:username>/', views.profile, name='profile'),
    path('<str:username>/<int:post_id>/', views.post_view, name='post'),
    path('<str:username>/<int:post_id>/edit/', views.post_edit, name='post_edit'), # noqa
    path('<str:username>/<int:post_id>/del/', views.post_del, name='post_del'), # noqa
    path('<str:username>/<int:post_id>/comment/', views.add_comment, name='add_comment'), # noqa
    path(
        '<str:username>/<int:post_id>/comment/<int:comment_id>/edit/',
        views.comment_edit,
        name='comment_edit'
    ),
    path(
        '<str:username>/<int:post_id>/comment/<int:comment_id>/del/',
        views.comment_del,
        name='comment_del'
    ),
]
