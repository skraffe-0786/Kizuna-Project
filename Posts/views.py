from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse

from .models import Post, Like, Comment, Share, SavedPost
from .forms import PostForm, CommentForm
from message_section.models import Notification, Conversation, Message


@login_required
def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related('user', 'user__profile').prefetch_related('comments__user'),
        id=post_id,
    )
    liked = Like.objects.filter(user=request.user, post=post).exists()
    saved = SavedPost.objects.filter(user=request.user, post=post).exists()
    return render(request, 'posts/post_detail.html', {
        'post': post,
        'liked': liked,
        'saved': saved,
    })


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect('home')
    return redirect('home')


@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
        if post.user != request.user:
            Notification.objects.create(
                user=post.user,
                sender=request.user,
                notification_type='like',
                post=post,
                text=f'{request.user.username} liked your post.',
            )
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'liked': liked, 'count': post.likes_count})
    next_url = request.GET.get('next') or request.POST.get('next', '')
    if next_url:
        return redirect(next_url)
    return redirect('home')


@login_required
def comment_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        poster_profile = post.user.profile
        pref = poster_profile.allow_comments
        allowed = True
        if post.user != request.user:
            if pref == 'nobody':
                allowed = False
            elif pref == 'following':
                allowed = request.user in poster_profile.followers.all()
        if not allowed:
            from django.contrib import messages as msg
            msg.error(request, 'Comments are restricted on this post.')
            next_url = request.POST.get('next', '')
            return redirect(next_url if next_url else 'home')
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.post = post
            comment.save()
            if post.user != request.user:
                Notification.objects.create(
                    user=post.user,
                    sender=request.user,
                    notification_type='comment',
                    post=post,
                    text=f'{request.user.username} commented on your post.',
                )
    next_url = request.POST.get('next', '')
    if next_url:
        return redirect(next_url)
    return redirect('home')


@login_required
def share_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    Share.objects.get_or_create(user=request.user, post=post)
    return redirect('home')


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = PostForm(instance=post)
    return render(request, 'posts/edit_post.html', {'form': form, 'post': post})


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)
    post.delete()
    return redirect('home')


@login_required
def save_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    saved, created = SavedPost.objects.get_or_create(user=request.user, post=post)
    if not created:
        saved.delete()
    next_url = request.GET.get('next', '')
    if next_url:
        return redirect(next_url)
    return redirect('home')


@login_required
def saved_posts(request):
    saved = SavedPost.objects.filter(user=request.user).select_related(
        'post', 'post__user', 'post__user__profile'
    )
    liked_ids = set(Like.objects.filter(user=request.user).values_list('post_id', flat=True))
    saved_ids = set(saved.values_list('post_id', flat=True))
    return render(request, 'posts/saved.html', {
        'saved': saved,
        'liked_ids': liked_ids,
        'saved_ids': saved_ids,
    })


@login_required
def search(request):
    from django.contrib.auth.models import User
    query = request.GET.get('q', '').strip()
    users = []
    posts = []
    if query:
        users = User.objects.filter(username__icontains=query).select_related('profile')[:10]
        posts = Post.objects.filter(caption__icontains=query).select_related('user', 'user__profile').prefetch_related('likes', 'comments')[:10]
    return render(request, 'search.html', {'query': query, 'users': users, 'posts': posts})


@login_required
def search_users_api(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'users': []})
    users = User.objects.filter(
        username__icontains=q
    ).exclude(id=request.user.id).select_related('profile')[:10]
    result = []
    for u in users:
        result.append({
            'username': u.username,
            'pic_url': u.profile.profile_pic.url if u.profile.profile_pic else '',
            'initial': u.username[0].upper(),
        })
    return JsonResponse({'users': result})


@login_required
def share_post_to_user(request, post_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=400)
    post = get_object_or_404(Post, id=post_id)
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
        shared_post=post,
    )
    conv.save()

    Share.objects.get_or_create(user=request.user, post=post)

    Notification.objects.create(
        user=target_user,
        sender=request.user,
        notification_type='message',
        text=f'{request.user.username} shared a post with you.',
    )
    return JsonResponse({'status': 'ok', 'message': f'Sent to {target_user.username}'})
