from django.urls import path

from . import views

urlpatterns = [
    path('create/', views.create_post, name='create_post'),
    path('<int:post_id>/', views.post_detail, name='post_detail'),
    path('<int:post_id>/like/', views.like_post, name='like_post'),
    path('<int:post_id>/comment/', views.comment_post, name='comment_post'),
    path('<int:post_id>/share/', views.share_post, name='share_post'),
    path('<int:post_id>/share-to/', views.share_post_to_user, name='share_post_to_user'),
    path('<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('<int:post_id>/save/', views.save_post, name='save_post'),
    path('saved/', views.saved_posts, name='saved_posts'),
    path('search/', views.search, name='search'),
    path('search-users/', views.search_users_api, name='search_users_api'),
]
