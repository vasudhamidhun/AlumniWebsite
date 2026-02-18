from .models import Notification

def notification_count(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return {}

    count = Notification.objects.filter(
        recipient_id=user_id,
        is_read=False
    ).count()

    return {'notification_count': count}


from .models import Message

def unread_message_count(request):
    user_id = request.session.get("user_id")

    if not user_id:
        return {}

    count = Message.objects.filter(
        receiver_id=user_id,
        is_read=False
    ).count()

    return {
        "unread_message_count": count
    }