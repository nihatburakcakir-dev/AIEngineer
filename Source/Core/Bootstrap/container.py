class Container:

    def __init__(self):

        self.services = {}

    def register(
        self,
        key,
        instance
    ):

        self.services[key] = instance

    def resolve(
        self,
        key
    ):

        return self.services.get(key)

    def exists(
        self,
        key
    ):

        return key in self.services
