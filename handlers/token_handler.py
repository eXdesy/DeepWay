# © 2025 eXdesy — All rights reserved.
# This code is for educational use only.
# Do not reuse, copy, modify, or redistribute.
import os
from dotenv import load_dotenv
import random
import string
from cryptography.fernet import Fernet

load_dotenv()
FERNET_TOKEN = os.getenv('FERNET_TOKEN')
fernet = Fernet(FERNET_TOKEN.encode())

def generate_token(telegram_id: int, status: str) -> str:
    token_data = f'{telegram_id}:{status}'
    encrypted_token = fernet.encrypt(token_data.encode()).decode()
    return encrypted_token

def generate_backup_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=5))

def decrypt_token(token):
    decrypted_data = fernet.decrypt(token.encode()).decode()
    current_telegram_id, status = decrypted_data.split(':')
    return current_telegram_id, status
