import re

class CSharpParser:

    FIELD_PATTERN = re.compile(
        r'(public|private|protected)\s+([\w<>]+)\s+(\w+)\s*=\s*(.+?);'
    )

    def fields(self, source):

        result = []

        for match in self.FIELD_PATTERN.finditer(source):

            result.append({

                "access": match.group(1),

                "type": match.group(2),

                "name": match.group(3),

                "value": match.group(4).strip(),

                "start": match.start(),

                "end": match.end()

            })

        return result

    def find_field(self, source, field):

        for item in self.fields(source):

            if item["name"] == field:
                return item

        return None
