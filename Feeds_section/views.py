from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse

from .models import Story, Reel, ReelLike, ReelComment, SavedReel
from .forms import StoryForm, ReelForm, ReelCommentForm
from message_section.models import Notification, Conversation, Message


@login_required
def create_story(request):
    if request.method == 'POST':
        form = StoryForm(request.POST, request.FILES)
        if form.is_valid():
            story = form.save(commit=False)
            story.user = request.user
            story.save()
    return redirect('home')


@login_required
def view_stories(request, user_id):
    from django.contrib.auth.models import User
    story_user = get_object_or_404(User, id=user_id)
    stories = Story.active_stories().filter(user=story_user)

    all_story_users = (
        Story.active_stories()
        .values_list('user_id', flat=True)
        .distinct()
    )
    story_user_ids = list(dict.fromkeys(all_story_users))
    current_idx = story_user_ids.index(user_id) if user_id in story_user_ids else 0
    prev_user = None
    next_user = None
    if current_idx > 0:
        prev_user = User.objects.select_related('profile').get(id=story_user_ids[current_idx - 1])
    if current_idx < len(story_user_ids) - 1:
        next_user = User.objects.select_related('profile').get(id=story_user_ids[current_idx + 1])

    return render(request, 'stories/view.html', {
        'story_user': story_user,
        'stories': stories,
        'prev_user': prev_user,
        'next_user': next_user,
    })


@login_required
def delete_story(request, story_id):
    story = get_object_or_404(Story, id=story_id, user=request.user)
    story.delete()
    remaining = Story.active_stories().filter(user=request.user).count()
    if remaining > 0:
        return redirect('view_stories', user_id=request.user.id)
    return redirect('home')


@login_required
def reply_story(request, user_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=400)
    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        return JsonResponse({'status': 'error', 'message': 'Cannot reply to your own story'}, status=400)
    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'status': 'error', 'message': 'Empty message'}, status=400)
    conv = Conversation.objects.filter(
        participants=request.user
    ).filter(participants=target_user).first()
    if not conv:
        conv = Conversation.objects.create()
        conv.participants.add(request.user, target_user)
    Message.objects.create(conversation=conv, sender=request.user, content=content)
    conv.save()
    Notification.objects.create(
        user=target_user,
        sender=request.user,
        notification_type='message',
        text=f'{request.user.username} replied to your story.',
    )
    return JsonResponse({'status': 'ok', 'message': 'Reply sent!'})


@login_required
def reels(request):
    all_reels = Reel.objects.select_related('user', 'user__profile').prefetch_related('reel_likes', 'reel_comments')[:20]
    reel_form = ReelForm()
    comment_form = ReelCommentForm()

    recent_convos = Conversation.objects.filter(
        participants=request.user
    ).prefetch_related('participants', 'participants__profile').order_by('-updated_at')[:10]
    recent_chat_users = []
    for conv in recent_convos:
        other = conv.participants.exclude(id=request.user.id).first()
        if other and other not in [u['user'] for u in recent_chat_users]:
            recent_chat_users.append({
                'user': other,
                'username': other.username,
                'pic_url': other.profile.profile_pic.url if other.profile.profile_pic else '',
                'initial': other.username[0].upper(),
            })

    reel_liked_ids = set(ReelLike.objects.filter(user=request.user).values_list('reel_id', flat=True))
    reel_saved_ids = set(SavedReel.objects.filter(user=request.user).values_list('reel_id', flat=True))

    return render(request, 'reels/reels.html', {
        'reels': all_reels,
        'reel_form': reel_form,
        'comment_form': comment_form,
        'recent_chat_users': recent_chat_users,
        'reel_liked_ids': reel_liked_ids,
        'reel_saved_ids': reel_saved_ids,
    })


@login_required
def reel_detail(request, reel_id):
    reel = get_object_or_404(
        Reel.objects.select_related('user', 'user__profile').prefetch_related('reel_likes', 'reel_comments__user'),
        id=reel_id,
    )
    liked = ReelLike.objects.filter(user=request.user, reel=reel).exists()
    saved = SavedReel.objects.filter(user=request.user, reel=reel).exists()
    comment_form = ReelCommentForm()
    return render(request, 'reels/reel_detail.html', {
        'reel': reel,
        'liked': liked,
        'saved': saved,
        'comment_form': comment_form,
    })


@login_required
def create_reel(request):
    if request.method == 'POST':
        form = ReelForm(request.POST, request.FILES)
        if form.is_valid():
            reel = form.save(commit=False)
            reel.user = request.user
            reel.save()
    return redirect('reels')


@login_required
def like_reel(request, reel_id):
    reel = get_object_or_404(Reel, id=reel_id)
    like, created = ReelLike.objects.get_or_create(user=request.user, reel=reel)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
        if reel.user != request.user:
            Notification.objects.create(
                user=reel.user,
                sender=request.user,
                notification_type='reel_like',
                reel=reel,
                text=f'{request.user.username} liked your reel.',
            )
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'liked': liked, 'count': reel.likes_count})
    next_url = request.GET.get('next') or request.POST.get('next', '')
    if next_url:
        return redirect(next_url)
    return redirect('reels')


@login_required
def comment_reel(request, reel_id):
    reel = get_object_or_404(Reel, id=reel_id)
    if request.method == 'POST':
        form = ReelCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.reel = reel
            comment.save()
            if reel.user != request.user:
                Notification.objects.create(
                    user=reel.user,
                    sender=request.user,
                    notification_type='reel_comment',
                    reel=reel,
                    text=f'{request.user.username} commented on your reel.',
                )
    next_url = request.POST.get('next', '')
    if next_url:
        return redirect(next_url)
    return redirect('reels')


@login_required
def share_reel_to_user(request, reel_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=400)
    reel = get_object_or_404(Reel, id=reel_id)
    username = request.POST.get('username', '')
    target_user = get_object_or_404(User, username=username)
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
        shared_reel=reel,
    )
    conv.save()

    Notification.objects.create(
        user=target_user,
        sender=request.user,
        notification_type='message',
        text=f'{request.user.username} shared a reel with you.',
    )
    return JsonResponse({'status': 'ok', 'message': f'Sent to {target_user.username}'})


@login_required
def edit_reel(request, reel_id):
    reel = get_object_or_404(Reel, id=reel_id, user=request.user)
    if request.method == 'POST':
        caption = request.POST.get('caption', '').strip()
        reel.caption = caption
        reel.save()
        next_url = request.POST.get('next', '')
        if next_url:
            return redirect(next_url)
        return redirect('reel_detail', reel_id=reel.id)
    return render(request, 'reels/edit_reel.html', {'reel': reel})


@login_required
def delete_reel(request, reel_id):
    reel = get_object_or_404(Reel, id=reel_id, user=request.user)
    reel.delete()
    next_url = request.POST.get('next') or request.GET.get('next', '')
    if next_url:
        return redirect(next_url)
    return redirect('home')


@login_required
def save_reel(request, reel_id):
    reel = get_object_or_404(Reel, id=reel_id)
    saved, created = SavedReel.objects.get_or_create(user=request.user, reel=reel)
    if not created:
        saved.delete()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'saved': created, 'count': reel.saved_by.count()})
    next_url = request.GET.get('next', '')
    if next_url:
        return redirect(next_url)
    return redirect('home')
