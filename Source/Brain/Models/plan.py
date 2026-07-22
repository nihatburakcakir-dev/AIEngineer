class Plan:

    def __init__(self):

        self.steps = []

    def add_step(

        self,

        step

    ):

        self.steps.append(step)

    def __iter__(self):

        return iter(self.steps)

    def __len__(self):

        return len(self.steps)
