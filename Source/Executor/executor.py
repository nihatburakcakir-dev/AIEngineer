from dataclasses import dataclass


@dataclass
class Command:

    action: str

    target: str

    effect: str = ""



class Executor:

    def execute(self, command: Command):

        print("=" * 60)
        print("EXECUTOR")
        print("=" * 60)

        print(command)

        print("=" * 60)
