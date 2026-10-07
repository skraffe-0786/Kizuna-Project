from django.urls import path

from . import views

urlpatterns = [
    path('edit/', views.edit_profile, name='edit_profile'),
    path('settings/', views.settings_view, name='settings'),
    path('settings/change-password/', views.change_password, name='change_password'),
    path('settings/save/', views.save_setting, name='save_setting'),
    path('settings/close-friends/search/', views.search_users_for_close_friends, name='search_close_friends'),
    path('settings/close-friends/toggle/', views.toggle_close_friend, name='toggle_close_friend'),
    path('settings/block/toggle/', views.toggle_block_user, name='toggle_block_user'),
    path('highlights/create/', views.create_highlight, name='create_highlight'),
    path('highlights/<int:highlight_id>/', views.view_highlight, name='view_highlight'),
    path('highlights/<int:highlight_id>/add/', views.add_highlight_item, name='add_highlight_item'),
    path('highlights/<int:highlight_id>/delete/', views.delete_highlight, name='delete_highlight'),
    path('<str:username>/', views.profile, name='profile'),
    path('<str:username>/follow/', views.follow_user, name='follow_user'),
    path('<str:username>/share-to/', views.share_profile_to_user, name='share_profile_to_user'),
]
