from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    COMMENT_CHOICES = [('everyone', 'Everyone'), ('following', 'People You Follow'), ('nobody', 'No One')]
    TAG_CHOICES = [('everyone', 'Everyone'), ('following', 'People You Follow'), ('nobody', 'No One')]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=300, blank=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True)
    followers = models.ManyToManyField(User, related_name='following_profiles', blank=True)

    is_private = models.BooleanField(default=False)
    allow_comments = models.CharField(max_length=10, choices=COMMENT_CHOICES, default='everyone')
    allow_tags = models.CharField(max_length=10, choices=TAG_CHOICES, default='everyone')
    close_friends = models.ManyToManyField(User, related_name='close_friend_of', blank=True)
    blocked_users = models.ManyToManyField(User, related_name='blocked_by', blank=True)

    def __str__(self):
        return self.user.username

    @property
    def followers_count(self):
        return self.followers.count()

    @property
    def following_count(self):
        return UserProfile.objects.filter(followers=self.user).count()

    @property
    def posts_count(self):
        return self.user.posts.count()


class Highlight(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='highlights')
    name = models.CharField(max_length=50)
    cover = models.ImageField(upload_to='highlights/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.name}'


class HighlightItem(models.Model):
    highlight = models.ForeignKey(Highlight, on_delete=models.CASCADE, related_name='items')
    image = models.ImageField(upload_to='highlights/items/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
