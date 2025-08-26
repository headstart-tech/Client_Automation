"""
This file contain class and functions related to encrypt or decrypt messages using cryptography
"""
import time
from pathlib import Path

from cryptography.fernet import Fernet


class EncryptionDecryption:
    """
    Contain functions related to encrypt or decrypt message activities
    """

    def generate_key(self):
        """
        Generates a key and save it into a file
        """
        key = Fernet.generate_key()
        with open("secret.key", "wb") as key_file:
            key_file.write(key)

    def load_key(self):
        """
        Load the previously generated key
        """
        return open("secret.key", "rb").read()

    def encrypt_message(self, message):
        """
        Encrypt a message
        """
        # -- Checks for Secret Key -- #
        if Path("secret.key").is_file():
            if Path("secret.key").stat().st_size == 0:
                self.generate_key()
        else:
            self.generate_key()
        key = self.load_key()
        encoded_message = message.encode()
        f = Fernet(key)
        encrypted_message = f.encrypt_at_time(encoded_message, int(time.time()))
        return encrypted_message

    async def decrypt_message(self, encrypted_message):
        """
        Decrypt an encrypted message
        """
        key = self.load_key()
        f = Fernet(key)
        encrypted_message = encrypted_message.encode()
        # Token will expire in 120 Hours
        decrypted_message = f.decrypt_at_time(encrypted_message, 1296000, int(time.time()))
        return decrypted_message.decode()

    async def encrypt_message_no_time(self, message):
        """
        Get the encrypted message without time token
        params:
            message (str):Get the message convert into encrypt message
        return:
            response (str): A message which has been encrypted
        """
        # -- Checks for Secret Key -- #
        if Path("secret.key").is_file():
            if Path("secret.key").stat().st_size == 0:
                self.generate_key()
        else:
            self.generate_key()
        key = self.load_key()
        encoded_message = message.encode()
        f = Fernet(key)
        encrypted_message = f.encrypt(encoded_message)
        return encrypted_message

    async def decrypt_message_no_time(self, encrypted_message):
        """
        decrypt the message into normal data from encrypted message

        params:
            encrypted_message (token): The encrypted message for decrypt

        return:
            response: A message which has been decrypted with normal data
        """
        key = self.load_key()
        f = Fernet(key)
        encrypted_message = encrypted_message.encode()
        decrypted_message = f.decrypt(encrypted_message)
        return decrypted_message.decode()
