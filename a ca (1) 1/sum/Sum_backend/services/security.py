# services/security.py

import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

# Load the key from your .env file
FERNET_KEY = os.getenv("FERNET_KEY")
if not FERNET_KEY:
    raise ValueError("FERNET_KEY not found in .env file. Please generate one.")

try:
    cipher_suite = Fernet(FERNET_KEY.encode())
except Exception as e:
    raise ValueError(f"Invalid FERNET_KEY, could not initialize cipher: {e}")

def encrypt_key(api_key: str) -> str:
    """Encrypts an API key."""
    if not api_key:
        return ""
    encrypted_text = cipher_suite.encrypt(api_key.encode())
    return encrypted_text.decode()

def decrypt_key(encrypted_api_key: str) -> str:
    """Decrypts an API key."""
    if not encrypted_api_key:
        return ""
    decrypted_text = cipher_suite.decrypt(encrypted_api_key.encode())
    return decrypted_text.decode()