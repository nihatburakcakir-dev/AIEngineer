class Memory:

    def __init__(self):

        self.variables = {}

        self.history_list = []

        self.undo_stack = []


    def set(self, key, value):

        self.variables[key] = value


    def get(self, key, default=None):

        return self.variables.get(key, default)


    def add_history(self, text):

        self.history_list.append(text)


    def history(self):

        return list(self.history_list)


    def push_undo(self, action):

        self.undo_stack.append(action)


    def pop_undo(self):

        if not self.undo_stack:

            return None

        return self.undo_stack.pop()


    def clear(self):

        self.variables.clear()

        self.history_list.clear()

        self.undo_stack.clear()
