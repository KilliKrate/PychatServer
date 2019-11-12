class Session:

    def __init__():
        self.__dict = {}

    def add(self, key, val):
        self.__dict[key] = val

    def remove(self, key):
        if key in self.__dict.keys():
            del self.__dict[key]