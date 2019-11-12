# IMPORTS
from Server import Server


# VARIABLES
SERVER_ADDRESS = ('172.16.3.224', 2000)


# METHODS
def main():

    server = Server(SERVER_ADDRESS)
    server.start()


# MAIN
if __name__ == '__main__':
    main()