from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from .models import Conversation, Message, Notification
from .forms import MessageForm


@login_required
def inbox(request):
    conversations = request.user.conversations.prefetch_related(
        'participants', 'participants__profile', 'messages'
    ).all()
    conv_list = []
    for conv in conversations:
        other = conv.participants.exclude(id=request.user.id).first()
        last_msg = conv.messages.last()
        unread = conv.messages.filter(is_read=False).exclude(sender=request.user).count()
        conv_list.append({'conversation': conv, 'other': other, 'last_msg': last_msg, 'unread': unread})
    return render(request, 'messages/inbox.html', {'conversations': conv_list})


@login_required
def conversation(request, username):
    other_user = get_object_or_404(User, username=username)
    my_profile = request.user.profile
    is_blocked = other_user in my_profile.blocked_users.all()
    is_blocked_by = request.user in other_user.profile.blocked_users.all()
    is_close_friend = other_user in my_profile.close_friends.all()
    messaging_blocked = is_blocked or is_blocked_by

    conv = Conversation.objects.filter(participants=request.user).filter(participants=other_user).first()

    if not conv:
        conv = Conversation.objects.create()
        conv.participants.add(request.user, other_user)

    if request.method == 'POST' and not messaging_blocked:
        form = MessageForm(request.POST)
        if form.is_valid():
            Message.objects.create(
                conversation=conv,
                sender=request.user,
                content=form.cleaned_data['content'],
            )
            conv.save()
            Notification.objects.create(
                user=other_user,
                sender=request.user,
                notification_type='message',
                text=f'{request.user.username} sent you a message.',
            )
            return redirect('conversation', username=username)
    else:
        form = MessageForm()

    conv.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    msgs = conv.messages.select_related(
        'sender', 'shared_post', 'shared_post__user', 'shared_post__user__profile',
        'shared_reel', 'shared_reel__user', 'shared_reel__user__profile',
        'shared_profile', 'shared_profile__profile',
    ).all()

    return render(request, 'messages/conversation.html', {
        'other_user': other_user,
        'messages_list': msgs,
        'form': form,
        'is_close_friend': is_close_friend,
        'is_blocked': is_blocked,
        'is_blocked_by': is_blocked_by,
        'messaging_blocked': messaging_blocked,
    })


@login_required
def unsend_message(request, message_id):
    msg = get_object_or_404(Message, id=message_id, sender=request.user)
    conv = msg.conversation
    other = conv.participants.exclude(id=request.user.id).first()
    msg.delete()
    return redirect('conversation', username=other.username)


@login_required
def notifications(request):
    notifs = request.user.notifications.select_related('sender', 'sender__profile').all()[:30]
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications.html', {'notifications': notifs})
