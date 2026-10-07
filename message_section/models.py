from django.db import models
from django.contrib.auth.models import User


class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField(max_length=1000, blank=True)
    shared_post = models.ForeignKey('Posts.Post', on_delete=models.SET_NULL, null=True, blank=True)
    shared_reel = models.ForeignKey('Feeds_section.Reel', on_delete=models.SET_NULL, null=True, blank=True)
    shared_profile = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='shared_in_messages')
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']


class Notification(models.Model):
    TYPES = [
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('follow', 'Follow'),
        ('message', 'Message'),
        ('reel_like', 'Reel Like'),
        ('reel_comment', 'Reel Comment'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    notification_type = models.CharField(max_length=20, choices=TYPES)
    text = models.TextField(max_length=200)
    post = models.ForeignKey('Posts.Post', on_delete=models.CASCADE, null=True, blank=True)
    reel = models.ForeignKey('Feeds_section.Reel', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
