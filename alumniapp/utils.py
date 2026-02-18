# utils.py
from django.core.mail import send_mail
from django.conf import settings
from cryptography.fernet import Fernet, InvalidToken


def get_cipher():
    return Fernet(settings.MESSAGE_SECRET_KEY)

def encrypt_message(text):
    return get_cipher().encrypt(text.encode()).decode()

def decrypt_message(text):
    try:
        return get_cipher().decrypt(text.encode()).decode()
    except InvalidToken:
        return "[Unable to decrypt message]"

def send_notification_email(subject, message, recipient_email):
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [recipient_email],
        fail_silently=True,
    )
