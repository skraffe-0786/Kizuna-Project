from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.http import JsonResponse

from .models import UserProfile, Highlight, HighlightItem
from .forms import ProfileEditForm, HighlightForm
from message_section.models import Notification, Conversation, Message


@login_required
def profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    user_profile = profile_user.profile
    is_following = request.user in user_profile.followers.all()
    is_own = request.user == profile_user
    is_private_locked = user_profile.is_private and not is_following and not is_own
    is_close_friend = not is_own and profile_user in request.user.profile.close_friends.all()
    is_blocked = not is_own and profile_user in request.user.profile.blocked_users.all()
    is_blocked_by = not is_own and request.user in user_profile.blocked_users.all()

    if is_blocked or is_blocked_by or is_private_locked:
        posts = profile_user.posts.none()
        highlights = profile_user.highlights.none()
    else:
        posts = profile_user.posts.prefetch_related('likes', 'comments').all()
        highlights = profile_user.highlights.prefetch_related('items')

    highlight_form = HighlightForm()
    return render(request, 'profile/profile.html', {
        'profile_user': profile_user,
        'user_profile': user_profile,
        'posts': posts,
        'highlights': highlights,
        'is_following': is_following,
        'highlight_form': highlight_form,
        'is_private_locked': is_private_locked,
        'is_close_friend': is_close_friend,
        'is_blocked': is_blocked,
        'is_blocked_by': is_blocked_by,
    })


@login_required
def edit_profile(request):
    user_profile = request.user.profile
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('profile', username=request.user.username)
    else:
        form = ProfileEditForm(instance=user_profile)
    return render(request, 'profile/edit.html', {'form': form})


@login_required
def follow_user(request, username):
    target_user = get_object_or_404(User, username=username)
    if target_user == request.user:
        return redirect('profile', username=username)

    target_profile = target_user.profile
    if request.user in target_profile.followers.all():
        target_profile.followers.remove(request.user)
    else:
        target_profile.followers.add(request.user)
        Notification.objects.create(
            user=target_user,
            sender=request.user,
            notification_type='follow',
            text=f'{request.user.username} started following you.',
        )
    return redirect('profile', username=username)


@login_required
def create_highlight(request):
    if request.method == 'POST':
        form = HighlightForm(request.POST, request.FILES)
        if form.is_valid():
            highlight = form.save(commit=False)
            highlight.user = request.user
            highlight.save()
    return redirect('profile', username=request.user.username)


@login_required
def view_highlight(request, highlight_id):
    highlight = get_object_or_404(Highlight, id=highlight_id)
    return render(request, 'profile/highlight.html', {'highlight': highlight})


@login_required
def add_highlight_item(request, highlight_id):
    highlight = get_object_or_404(Highlight, id=highlight_id, user=request.user)
    if request.method == 'POST' and request.FILES.get('image'):
        HighlightItem.objects.create(highlight=highlight, image=request.FILES['image'])
    return redirect('view_highlight', highlight_id=highlight.id)


@login_required
def delete_highlight(request, highlight_id):
    highlight = get_object_or_404(Highlight, id=highlight_id, user=request.user)
    username = highlight.user.username
    highlight.delete()
    return redirect('profile', username=username)


@login_required
def settings_view(request):
    from Posts.models import SavedPost
    saved_posts = SavedPost.objects.filter(user=request.user).select_related('post', 'post__user', 'post__user__profile')
    profile = request.user.profile
    close_friends = profile.close_friends.select_related('profile').all()
    blocked_users = profile.blocked_users.select_related('profile').all()
    return render(request, 'profile/settings.html', {
        'saved_posts': saved_posts,
        'close_friends': close_friends,
        'blocked_users': blocked_users,
    })


@login_required
def save_setting(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=400)
    profile = request.user.profile
    key = request.POST.get('key', '')
    value = request.POST.get('value', '')

    if key == 'is_private':
        profile.is_private = value == 'true'
        profile.save(update_fields=['is_private'])
    elif key == 'allow_comments':
        if value in ('everyone', 'following', 'nobody'):
            profile.allow_comments = value
            profile.save(update_fields=['allow_comments'])
    elif key == 'allow_tags':
        if value in ('everyone', 'following', 'nobody'):
            profile.allow_tags = value
            profile.save(update_fields=['allow_tags'])
    else:
        return JsonResponse({'status': 'error', 'message': 'Unknown setting'}, status=400)

    return JsonResponse({'status': 'ok'})


@login_required
def search_users_for_close_friends(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 1:
        return JsonResponse({'users': []})
    users = User.objects.filter(
        username__icontains=q
    ).exclude(id=request.user.id).select_related('profile')[:10]
    close_ids = set(request.user.profile.close_friends.values_list('id', flat=True))
    result = []
    for u in users:
        result.append({
            'id': u.id,
            'username': u.username,
            'pic': u.profile.profile_pic.url if u.profile.profile_pic else '',
            'is_close': u.id in close_ids,
        })
    return JsonResponse({'users': result})


@login_required
def toggle_close_friend(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=400)
    user_id = request.POST.get('user_id')
    target = get_object_or_404(User, id=user_id)
    profile = request.user.profile
    if target in profile.close_friends.all():
        profile.close_friends.remove(target)
        added = False
    else:
        profile.close_friends.add(target)
        added = True
    return JsonResponse({'status': 'ok', 'added': added})


@login_required
def toggle_block_user(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=400)
    user_id = request.POST.get('user_id')
    target = get_object_or_404(User, id=user_id)
    if target == request.user:
        return JsonResponse({'status': 'error', 'message': 'Cannot block yourself'}, status=400)
    profile = request.user.profile
    if target in profile.blocked_users.all():
        profile.blocked_users.remove(target)
        blocked = False
    else:
        profile.blocked_users.add(target)
        profile.followers.remove(target)
        target.profile.followers.remove(request.user)
        profile.close_friends.remove(target)
        blocked = True
    return JsonResponse({'status': 'ok', 'blocked': blocked})


@login_required
def share_profile_to_user(request, username):
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=400)
    profile_user = get_object_or_404(User, username=username)
    target_username = request.POST.get('username', '')
    target_user = get_object_or_404(User, username=target_username)
    if target_user == request.user:
        return JsonResponse({'status': 'error', 'message': 'Cannot share to yourself'}, status=400)

    conv = Conversation.objects.filter(
        participants=request.user
    ).filter(participants=target_user).first()
    if not conv:
        conv = Conversation.objects.create()
        conv.participants.add(request.user, target_user)

    Message.objects.create(
        conversation=conv,
        sender=request.user,
        shared_profile=profile_user,
    )
    conv.save()

    Notification.objects.create(
        user=target_user,
        sender=request.user,
        notification_type='message',
        text=f'{request.user.username} shared a profile with you.',
    )
    return JsonResponse({'status': 'ok', 'message': f'Sent to {target_user.username}'})


@login_required
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
        elif len(new_password) < 8:
            messages.error(request, 'New password must be at least 8 characters.')
        elif new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
        else:
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Password changed successfully!')
            return redirect('settings')
    return render(request, 'profile/change_password.html')
