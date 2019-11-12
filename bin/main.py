# IMPORTS
import socket
from Server import Server


# VARIABLES
SERVER_ADDRESS = ('localhost', 2000)


# METHODS
def main():

    server = Server(SERVER_ADDRESS)
    server.start()


# MAIN
if __name__ == '__main__':
    main()