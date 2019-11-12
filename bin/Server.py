# IMPORTS
import socket
import sqlite3
import hashlib
from datetime import datetime
from ClientConnection import ClientConnection
from ClientSession import ClientSession


# CLASS
class Server:

    DB_INIT = "CREATE TABLE User(id INTEGER PRIMARY KEY, username VARCHAR(16) UNIQUE, password VARCHAR(16))"

    class UserNotFoundException(Exception):
        pass

    class AlreadyUserException(Exception):
        pass

    class InvalidPasswordException(Exception):
        pass

    def __init__(self, address):

        self._address = address
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self._db_conn = sqlite3.connect(':memory:', check_same_thread=False)
        self._db_cursor = self._db_conn.cursor()

        self._sessions = {}

    def start(self):

        self._db_cursor.execute(self.DB_INIT)

        self.__socket.bind(self._address)
        self.__socket.listen(5)

        while True:
            (destination_socket, destination_address) = self.__socket.accept()

            print(
                f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - {destination_address[0]}')

            thread_session = ClientSession()

            t = ClientConnection(destination_socket, self, thread_session)
            t.start()

            print(f'Currently logged: {len(self._sessions)}')

    def _user_logged(self, username):
        for thread_id, thread_username in self._sessions.items():
            if username == thread_username:
                return thread_id
        return -1

    def signup(self, thread_self, username, password):

        hash_password = hashlib.sha256(password.encode()).hexdigest()

        try:
            self._db_cursor.execute(
                "INSERT INTO User(username, password) VALUES(?, ?)", (username, hash_password))
        except:
            raise Server.AlreadyUserException()

    def signin(self, thread_self, username, password):

        hash_password = hashlib.sha256(password.encode()).hexdigest()

        self._db_cursor.execute(
            "SELECT password FROM User WHERE username = ?", (username, ))

        try:
            psw = self._db_cursor.fetchone()[0]
            if hash_password != psw:
                raise Server.InvalidPasswordException()
        except TypeError:
            raise Server.UserNotFoundException()

    def logout(self, thread_self, username):
        self._sessions.pop(thread_self.ident, None)

    def send_private(self, thread_self, username, text):
        print(self._user_logged('username'))

    def user_list(self):
        users = []
        for session in self._sessions:
            if 'username' in session.keys():
                users.append(session['username'])
        return users
