from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

def get_cipher():
    return Fernet(settings.MESSAGE_SECRET_KEY)

def encrypt_message(text):
    return get_cipher().encrypt(text.encode()).decode()

def decrypt_message(text):
    try:
        return get_cipher().decrypt(text.encode()).decode()
    except InvalidToken:
        return "[Unable to decrypt message]"
