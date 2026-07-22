class Router:

    def __init__(self):

        self.handlers = []

    def register(self, handler):

        self.handlers.append(handler)

    def resolve(self, intent):

        for handler in self.handlers:

            if handler.can_handle(intent):

                return handler

        return None
