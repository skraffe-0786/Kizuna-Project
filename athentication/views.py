from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages

from .forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
            )
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            if not User.objects.filter(username__iexact=username).exists():
                form.add_error('username', 'This username does not exist.')
            else:
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.username}!')
                    return redirect('home')
                else:
                    form.add_error('password', 'Incorrect password. Please try again.')
    else:
        form = LoginForm()
    return render(request, 'auth/login.html', {'form': form})


def forgot_password(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            user = User.objects.get(username__iexact=username)
            request.session['reset_user_id'] = user.id
            return redirect('reset_password')
    else:
        form = ForgotPasswordForm()
    return render(request, 'auth/forgot_password.html', {'form': form})


def reset_password(request):
    user_id = request.session.get('reset_user_id')
    if not user_id:
        messages.error(request, 'Please verify your identity first.')
        return redirect('forgot_password')

    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['new_password'])
            user.save()
            del request.session['reset_user_id']
            messages.success(request, 'Password reset successfully! Please log in.')
            return redirect('login')
    else:
        form = ResetPasswordForm()
    return render(request, 'auth/reset_password.html', {'form': form, 'reset_user': user})


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')


def home(request):
    if not request.user.is_authenticated:
        return redirect('login')

    from Posts.models import Post
    from Feeds_section.models import Story, Reel, ReelLike, SavedReel
    from Posts.forms import PostForm, CommentForm
    from Feeds_section.forms import StoryForm, ReelCommentForm
    from message_section.models import Notification

    from Posts.models import Like
    from Profile.models import UserProfile

    posts = Post.objects.select_related('user', 'user__profile').prefetch_related('likes', 'comments__user').all()[:20]
    reels = Reel.objects.select_related('user', 'user__profile').prefetch_related('reel_likes', 'reel_comments__user')[:10]
    reel_liked_ids = set(ReelLike.objects.filter(user=request.user).values_list('reel_id', flat=True))
    reel_saved_ids = set(SavedReel.objects.filter(user=request.user).values_list('reel_id', flat=True))

    feed_items = []
    for p in posts:
        feed_items.append({'type': 'post', 'item': p, 'date': p.created_at})
    for r in reels:
        feed_items.append({'type': 'reel', 'item': r, 'date': r.created_at})
    feed_items.sort(key=lambda x: x['date'], reverse=True)
    stories = Story.active_stories().select_related('user', 'user__profile')
    from Posts.models import SavedPost
    liked_ids = set(Like.objects.filter(user=request.user).values_list('post_id', flat=True))
    saved_ids = set(SavedPost.objects.filter(user=request.user).values_list('post_id', flat=True))

    following_ids = UserProfile.objects.filter(followers=request.user).values_list('user_id', flat=True)
    suggested_users = User.objects.exclude(
        id__in=list(following_ids) + [request.user.id]
    ).select_related('profile')[:5]

    post_form = PostForm()
    story_form = StoryForm()
    comment_form = CommentForm()
    unread_notifications = request.user.notifications.filter(is_read=False).count()
    unread_messages = request.user.conversations.filter(
        messages__is_read=False
    ).exclude(messages__sender=request.user).distinct().count()

    from message_section.models import Conversation
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

    import re
    tracked_tags = {
        'onepiece': 'OnePiece',
        'naruto': 'Naruto',
        'demonslayer': 'DemonSlayer',
        'sololeveling': 'SoloLeveling',
        'bleach': 'Bleach',
        'jjk': 'JJK',
        'jujutsukaisen': 'JujutsuKaisen',
        'dragonball': 'DragonBall',
        'dragonballz': 'DragonBallZ',
        'tokyorevengers': 'TokyoRevengers',
        'attackontitan': 'AttackOnTitan',
        'aot': 'AOT',
        'deathnote': 'DeathNote',
        'myheroacademia': 'MyHeroAcademia',
        'mha': 'MHA',
        'chainsawman': 'ChainsawMan',
        'spyxfamily': 'SpyXFamily',
        'onepunchman': 'OnePunchMan',
        'hunterxhunter': 'HunterXHunter',
        'blackclover': 'BlackClover',
        'vinlandsaga': 'VinlandSaga',
        'fullmetalalchemist': 'FullmetalAlchemist',
        'fmab': 'FMAB',
        'tokyoghoul': 'TokyoGhoul',
        'swordartonline': 'SwordArtOnline',
        'sao': 'SAO',
        'fairytail': 'FairyTail',
        'haikyuu': 'Haikyuu',
        'kuroko': 'Kuroko',
        'mushokutensei': 'MushokuTensei',
        'rezero': 'ReZero',
        'konosuba': 'Konosuba',
        'overlord': 'Overlord',
        'mob100': 'Mob100',
        'mobpsycho': 'MobPsycho',
        'frieren': 'Frieren',
        'dandadan': 'Dandadan',
        'bluelock': 'BlueLock',
        'kaijuno8': 'KaijuNo8',
        'windbreaker': 'WindBreaker',
        'shangrilaFrontier': 'ShangriFrontier',
        'evangelion': 'Evangelion',
        'cowboybebop': 'CowboyBebop',
        'steinsgate': 'SteinsGate',
        'codegeass': 'CodeGeass',
        'gintama': 'Gintama',
        'berserk': 'Berserk',
        'inuyasha': 'Inuyasha',
        'anime': 'Anime',
        'manga': 'Manga',
        'otaku': 'Otaku',
        'waifu': 'Waifu',
    }
    tag_counts = {k: 0 for k in tracked_tags}
    all_captions = Post.objects.values_list('caption', flat=True)
    for caption in all_captions:
        if caption:
            found = re.findall(r'#(\w+)', caption)
            for t in found:
                key = t.lower()
                if key in tag_counts:
                    tag_counts[key] += 1

    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    trending_tags = []
    for rank, (key, count) in enumerate(sorted_tags, 1):
        trending_tags.append({
            'rank': rank,
            'tag': tracked_tags[key],
            'display': f'#{tracked_tags[key]}',
            'count': count,
        })

    context = {
        'posts': posts,
        'feed_items': feed_items,
        'reel_liked_ids': reel_liked_ids,
        'reel_saved_ids': reel_saved_ids,
        'stories': stories,
        'liked_ids': liked_ids,
        'saved_ids': saved_ids,
        'suggested_users': suggested_users,
        'post_form': post_form,
        'story_form': story_form,
        'comment_form': comment_form,
        'reel_comment_form': ReelCommentForm(),
        'unread_notifications': unread_notifications,
        'unread_messages': unread_messages,
        'recent_chat_users': recent_chat_users,
        'trending_tags': trending_tags,
    }
    return render(request, 'home.html', context)
