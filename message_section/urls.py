from django.urls import path

from . import views

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('notifications/', views.notifications, name='notifications'),
    path('unsend/<int:message_id>/', views.unsend_message, name='unsend_message'),
    path('<str:username>/', views.conversation, name='conversation'),
]
