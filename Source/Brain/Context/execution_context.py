class ExecutionContext:

    def __init__(self):

        self.project = None

        self.workspace = None

        self.script = None

        self.script_path = None

        self.file_content = None

        self.patch = None

        self.compile_result = None

        self.validation_result = None

        self.shared = {}

    def set(self, key, value):

        self.shared[key] = value

    def get(self, key, default=None):

        return self.shared.get(key, default)
