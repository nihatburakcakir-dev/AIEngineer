from Source.Core.Models.command import AICommand
from Source.Core.Parser.intent_parser import IntentParser

class CommandParser:

    def __init__(self):
        self.intent_parser = IntentParser()

    def parse(self, text: str) -> AICommand:

        cmd = AICommand()

        cmd.prompt = text
        cmd.intent = self.intent_parser.parse(text)

        t = text.lower()

        keywords = {
            "wolf":"Wolf",
            "kurt":"Wolf",
            "kurd":"Wolf",

            "ball":"Ball",
            "top":"Ball",

            "camera":"Camera",
            "kamera":"Camera",

            "cube":"Cube",
            "küp":"Cube",

            "sphere":"Sphere",
            "küre":"Sphere",

            "capsule":"Capsule",

            "ui":"UI",
            "canvas":"Canvas",
            "menu":"Menu",

            "prefab":"Prefab",
            "scene":"Scene",
            "script":"Script",
            "material":"Material",
            "sprite":"Sprite",

            "zuma":"MarbleShooter"
        }

        for k, v in keywords.items():
            if k in t:
                cmd.target = v
                break

        if "göz" in t:
            cmd.parameters["part"] = "Eyes"

        colors = {
            "kırmızı":"Red",
            "mavi":"Blue",
            "yeşil":"Green",
            "sarı":"Yellow",
            "siyah":"Black",
            "beyaz":"White"
        }

        for k, v in colors.items():
            if k in t:
                cmd.parameters["color"] = v
                if cmd.intent == "MODIFY_OBJECT":
                    cmd.intent = "CHANGE_COLOR"
                break

        return cmd
