from Source.Brain.Models.intent import Intent


class IntentParser:

    def parse(
        self,
        text
    ):

        lower = text.lower()

        if any(
            word in lower
            for word in [

                "speed",
                "velocity",
                "hız"

            ]
        ):

            return Intent(

                name="modify_variable",

                target="BallChainManager",

                action="multiply",

                parameters={

                    "variable":"speed"

                },

                confidence=0.70,

                reasoning="Keyword matched."

            )

        return Intent(

            name="unknown",

            confidence=0.0
        )
