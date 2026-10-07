from django.urls import path

from . import views

urlpatterns = [
    path('stories/create/', views.create_story, name='create_story'),
    path('stories/<int:user_id>/', views.view_stories, name='view_stories'),
    path('stories/<int:story_id>/delete/', views.delete_story, name='delete_story'),
    path('stories/<int:user_id>/reply/', views.reply_story, name='reply_story'),
    path('reels/', views.reels, name='reels'),
    path('reels/create/', views.create_reel, name='create_reel'),
    path('reels/<int:reel_id>/view/', views.reel_detail, name='reel_detail'),
    path('reels/<int:reel_id>/like/', views.like_reel, name='like_reel'),
    path('reels/<int:reel_id>/comment/', views.comment_reel, name='comment_reel'),
    path('reels/<int:reel_id>/share-to/', views.share_reel_to_user, name='share_reel_to_user'),
    path('reels/<int:reel_id>/edit/', views.edit_reel, name='edit_reel'),
    path('reels/<int:reel_id>/delete/', views.delete_reel, name='delete_reel'),
    path('reels/<int:reel_id>/save/', views.save_reel, name='save_reel'),
]
