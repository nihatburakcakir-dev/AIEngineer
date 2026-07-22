import re

from Source.Core.CodeModel.script import ScriptModel
from Source.Core.CodeModel.class_model import ClassModel
from Source.Core.CodeModel.field_model import FieldModel
from Source.Core.CodeModel.method_model import MethodModel
from Source.Core.CodeModel.property_model import PropertyModel


class CodeParser:

    CLASS_PATTERN = re.compile(
        r'class\s+(\w+)(?:\s*:\s*([\w<>,.\s]+?))?\s*\{'
    )

    # Field with an initializer: access modifier, type, name, "= value;"
    FIELD_WITH_VALUE_PATTERN = re.compile(
        r'(?:\[[^\]]*\]\s*)*'
        r'(public|private|protected|internal)\s+'
        r'(?:static\s+|readonly\s+)*'
        r'([\w<>\[\],\s]+?)\s+(\w+)\s*=\s*([^;]+);'
    )

    # Field without an initializer: access modifier, type, name, ";"
    FIELD_NO_VALUE_PATTERN = re.compile(
        r'(?:\[[^\]]*\]\s*)*'
        r'(public|private|protected|internal)\s+'
        r'(?:static\s+|readonly\s+)*'
        r'([\w<>\[\],\s]+?)\s+(\w+)\s*;'
    )

    # Method declaration: optional access modifier (Unity events may omit it),
    # optional static/virtual/override/abstract, return type, name, params, then "{" or ";"
    METHOD_PATTERN = re.compile(
        r'(public|private|protected|internal)?\s*'
        r'(?:static\s+|virtual\s+|override\s+|abstract\s+|sealed\s+|async\s+)*'
        r'(IEnumerator|void|bool|int|float|double|string|long|byte|char|object'
        r'|[A-Z]\w*(?:<[\w<>\[\],\s]+>)?(?:\[\])?)\s+'
        r'(\w+)\s*\(([^)]*)\)\s*(?:\{|;)'
    )

    # Property declaration: access modifier, type, name, "{ get; set; }" style body
    PROPERTY_PATTERN = re.compile(
        r'(public|private|protected|internal)\s+'
        r'(?:static\s+|virtual\s+|override\s+|abstract\s+)*'
        r'([\w<>\[\],\s]+?)\s+(\w+)\s*'
        r'\{\s*(?:get|set)\b[^}]*\}'
    )

    def parse(self, path):
        """Parse class-level members without mistaking method locals for fields."""
        with open(path, "r", encoding="utf-8-sig", errors="ignore") as source_file:
            text = source_file.read()

        script = ScriptModel()
        script.path = str(path)
        masked = self._mask_comments_and_strings(text)

        for match in self.CLASS_PATTERN.finditer(masked):
            body_end = self._find_closing_brace(masked, match.end() - 1)
            if body_end is None:
                continue

            cls = ClassModel()
            cls.name = match.group(1)
            inheritance = (match.group(2) or "").strip()
            cls.base_class = inheritance.split(",")[0].strip() if inheritance else ""
            self._parse_class_members(cls, text[match.end():body_end], masked[match.end():body_end])
            script.classes.append(cls)

        return script

    @staticmethod
    def _mask_comments_and_strings(text):
        pattern = re.compile(
            r'//[^\r\n]*|/\*[\s\S]*?\*/|@?"(?:""|\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''
        )
        return pattern.sub(lambda item: re.sub(r"[^\r\n]", " ", item.group(0)), text)

    @staticmethod
    def _find_closing_brace(text, opening_brace):
        depth = 0
        for index in range(opening_brace, len(text)):
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
                if depth == 0:
                    return index
        return None

    @staticmethod
    def _top_level_members(text):
        start = 0
        depth = 0
        for index, character in enumerate(text):
            if character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth == 0:
                    yield text[start:index + 1]
                    start = index + 1
            elif character == ";" and depth == 0:
                yield text[start:index + 1]
                start = index + 1

    def _parse_class_members(self, cls, source, masked):
        field_pattern = re.compile(
            r"^(?:\s*\[[^\]]+\]\s*)*\s*(public|private|protected|internal)\s+"
            r"(?:(?:static|readonly|const|volatile)\s+)*([\w.<>\[\],\s]+?)\s+(\w+)\s*(?:=.*)?;$",
            re.DOTALL,
        )
        property_pattern = re.compile(
            r"^\s*(public|private|protected|internal)\s+(?:static\s+)?([\w.<>\[\],\s]+?)\s+(\w+)\s*\{\s*(?:get|set|init)\b",
            re.DOTALL,
        )
        method_pattern = re.compile(
            r"^\s*(?:(public|private|protected|internal)\s+)?"
            r"(?:(?:static|virtual|override|abstract|sealed|async)\s+)*"
            r"([\w.]+(?:\s*<[^(){};]+>)?(?:\[\])?)\s+(\w+)\s*\((.*?)\)",
            re.DOTALL,
        )

        source_members = list(self._top_level_members(source))
        masked_members = list(self._top_level_members(masked))
        for source_member, masked_member in zip(source_members, masked_members):
            property_match = property_pattern.match(masked_member)
            if property_match:
                prop = PropertyModel()
                prop.access = property_match.group(1)
                prop.type = property_match.group(2).strip()
                prop.name = property_match.group(3)
                cls.properties.append(prop)
                continue

            method_match = method_pattern.match(masked_member)
            if method_match:
                method = MethodModel()
                method.access = method_match.group(1) or "private"
                method.return_type = method_match.group(2).strip()
                method.name = method_match.group(3)
                parameters = method_match.group(4).strip()
                method.parameters = [value.strip() for value in parameters.split(",")] if parameters else []
                cls.methods.append(method)
                continue

            field_match = field_pattern.match(masked_member)
            if field_match:
                field = FieldModel()
                field.access = field_match.group(1)
                field.type = field_match.group(2).strip()
                field.name = field_match.group(3)
                value_match = re.search(r"=\s*(.*);\s*$", source_member, re.DOTALL)
                field.value = value_match.group(1).strip() if value_match else ""
                cls.fields.append(field)

    def parse_legacy(self, path):

        with open(path, "r", encoding="utf-8", errors="ignore") as f:

            text = f.read()

        script = ScriptModel()

        script.path = path

        for match in self.CLASS_PATTERN.finditer(text):

            cls = ClassModel()

            cls.name = match.group(1)

            inherits = match.group(2) or ""

            # First entry after ':' is the base class by Unity/C# convention;
            # remaining entries (if any) are interfaces and are ignored here.
            first = inherits.split(",")[0].strip() if inherits else ""

            cls.base_class = first

            script.classes.append(cls)

        if not script.classes:

            return script

        # NOTE: fields/methods/properties are attached to the first class only.
        # This matches the original behaviour and is sufficient for the common
        # Unity case of one MonoBehaviour class per file.
        cls = script.classes[0]

        seen_fields = set()

        for match in self.FIELD_WITH_VALUE_PATTERN.finditer(text):

            field = FieldModel()

            field.access = match.group(1)

            field.type = match.group(2).strip()

            field.name = match.group(3)

            field.value = match.group(4).strip()

            cls.fields.append(field)

            seen_fields.add(field.name)

        for match in self.FIELD_NO_VALUE_PATTERN.finditer(text):

            name = match.group(3)

            if name in seen_fields:
                continue

            field = FieldModel()

            field.access = match.group(1)

            field.type = match.group(2).strip()

            field.name = name

            field.value = ""

            cls.fields.append(field)

            seen_fields.add(name)

        for match in self.PROPERTY_PATTERN.finditer(text):

            prop = PropertyModel()

            prop.access = match.group(1)

            prop.type = match.group(2).strip()

            prop.name = match.group(3)

            cls.properties.append(prop)

        seen_methods = set()

        for match in self.METHOD_PATTERN.finditer(text):

            name = match.group(3)

            params = match.group(4).strip()

            key = (name, params)

            if key in seen_methods:
                continue

            seen_methods.add(key)

            method = MethodModel()

            method.access = match.group(1) or "private"

            method.return_type = match.group(2)

            method.name = name

            method.parameters = (
                [p.strip() for p in params.split(",")]
                if params
                else []
            )

            cls.methods.append(method)

        return script
