from Source.Core.Executor.file_executor import FileExecutor
from Source.Core.Executor.csharp_parser import CSharpParser

class PatchApplier:

    def __init__(self):

        self.files = FileExecutor()
        self.parser = CSharpParser()

    def apply(self, patch):

        source = self.files.read(
            patch.file
        )

        field = self.parser.find_field(
            source,
            patch.target
        )

        if field is None:

            return False

        old_line = source[
            field["start"]:
            field["end"]
        ]

        if patch.operation == "multiply":

            try:

                value = field["value"]

                if value.endswith("f"):
                    value = value[:-1]

                number = float(value)

                number *= float(patch.value)

                new_value = str(round(number, 4)) + "f"

            except:

                return False

        elif patch.operation == "set":

            new_value = str(patch.value)

        else:

            return False

        new_line = old_line.replace(
            field["value"],
            new_value
        )

        source = (
            source[:field["start"]]
            + new_line
            + source[field["end"]:]
        )

        self.files.write(
            patch.file,
            source
        )

        return True
