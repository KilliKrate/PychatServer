# IMPORTS
import threading
import sqlite3
import socket
import time
import sys
import re


# CLASS
class ClientConnection(threading.Thread):

    PACKET_TYPES = {
        0: 'confirm',
        1: 'error',
        10: 'signup',
        11: 'signin',
        12: 'logout',
        22: 'private',
    }
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9#*-_$]{4,30}$')
    PASSWORD_PATTERN = re.compile(r'^[a-zA-Z0-9#*-_$]{6,30}$')

    def __init__(self, client_socket, server_instance):
        self._client_socket = client_socket
        self._server_instance = server_instance
        self._session = {}
        threading.Thread.__init__(self)

    def _listen_client(self):

        try:
            response = self._client_socket.recv(1024)
        except:
            print('error')
        return response

    def _unpack_chat_packet(self, packet):

        if len(packet) < 3:
            raise Exception

        p_type, p_len, payload = self.PACKET_TYPES[packet[0]], int.from_bytes(
            packet[1:3], 'big'), []

        if len(packet) > 3:
            payload = packet[3:]

        return p_type, p_len, payload

    def run(self):

        while True:

            packet = self._listen_client()

            if packet == b'':
                break

            try:
                p_type, p_len, payload = self._unpack_chat_packet(packet)
            except Exception as e:
                print(e)
                print("Pacchetto non valido")
                break

            #print(f'Received a packet')
            print(f'Packet: {p_type}')
            #print(f'\tpayload: {payload}\n')

            getattr(self, f'_{p_type}')(payload)

        self._logout(forced=True)
        print("Connessione chiusa. Logout forzato")

        return False

    def _create_packet(self, number, *payload):
        if type(number) != int:
            return

        bytes_payload = self._concatenate_bytes(*payload)
        bytes_payload_len = len(bytes_payload).to_bytes(2, 'big')

        return self._concatenate_bytes(number, bytes_payload_len, bytes_payload)

    def _confirm(self):
        packet = self._create_packet(0)
        self._client_socket.send(packet)

    def _error(self, description):
        packet = self._create_packet(1, description)
        self._client_socket.send(packet)

    def _confirm_logout(self, username):
        packet = self._create_packet(44, username)
        self._client_socket.send(packet)

    def _is_logged(self):
        if 'username' in self._session.keys():
            return True
        return False

    def _signup(self, payload):

        if self._is_logged():
            return self._error("Sei già loggato. Effettuare il logout prima di registrare un nuovo account.")

        username, password = [elem.decode('utf-8')
                              for elem in payload.split(b'\x00')]

        if not self.USERNAME_PATTERN.match(username):
            return self._error('Username non valido.')
        if not self.PASSWORD_PATTERN.match(password):
            return self._error('Password non valida.')

        try:
            self._server_instance.signup(self, username, password)
            self._confirm()
        except self._server_instance.AlreadyUserException:
            self._error("Questo username esiste già")

    def _signin(self, payload):

        if self._is_logged():
            return self._error("Sei già loggato, impossibile effettuare un altro login.")

        if len(payload) < 2:
            return self._error("Si è verificato un errore durante il login.")

        username, password = [elem.decode('utf-8')
                              for elem in payload.split(b'\x00')]

        try:
            self._server_instance.signin(self, username, password)
            self._confirm()
            self._session['username'] = username
        except self._server_instance.UserNotFoundException:
            self._error("L'account non esiste.")
        except self._server_instance.InvalidPasswordException:
            self._error("La password non è corretta.")

    def _logout(self, forced=False):

        if self._is_logged():
            username = self._session.get('username', '')
            self._session = {}
            if not forced:
                self._confirm()
                self._confirm_logout(username)
            self._server_instance.logout(self, username)
        else:
            if not forced:
                self._error(
                    'Attualmente non sei loggato, impossibile effettuare il logout.')

    def _private(self, payload):

        if not self._is_logged():
            return self._error("Non sei loggato. Effettua il login prima di spedire un messaggio.")

        username, text = [elem.decode('utf-8')
                          for elem in payload.split(b'\x00')]

        self._server_instance.send_private(self, username, text)

    def _send_private(self):
        pass

    def _concatenate_bytes(self, *args):

        res = bytearray()

        for arg in args:
            if type(arg) == bytes or type(arg) == bytearray:
                res += arg
            elif type(arg) == str:
                res += arg.encode()
            elif type(arg) == int:
                res.append(arg)

        return res
