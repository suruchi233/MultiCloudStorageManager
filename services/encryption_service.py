from cryptography.fernet import Fernet
import os

KEY_FILE = "secret.key"


def load_key():

    if not os.path.exists(KEY_FILE):

        key = Fernet.generate_key()

        with open(KEY_FILE, "wb") as f:
            f.write(key)

    with open(KEY_FILE, "rb") as f:
        return f.read()


key = load_key()

cipher = Fernet(key)


def encrypt_file(file_path):

    with open(file_path, "rb") as file:
        data = file.read()

    encrypted_data = cipher.encrypt(data)

    with open(file_path, "wb") as file:
        file.write(encrypted_data)


def decrypt_file(file_path):

    with open(file_path, "rb") as file:
        data = file.read()

    decrypted_data = cipher.decrypt(data)

    with open(file_path, "wb") as file:
        file.write(decrypted_data)