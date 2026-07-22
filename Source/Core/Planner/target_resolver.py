class TargetResolver:

    def resolve(self, command, matches):

        if len(matches) == 0:
            return None

        if len(matches) == 1:
            return matches[0]

        target = command.target.lower()

        priority = {

            "ball":[
                "BallChainManager",
                "BallShooter",
                "SplineMover"
            ],

            "wolf":[
                "HealthManager"
            ]
        }

        if target in priority:

            for cls in priority[target]:

                for m in matches:

                    if m["class"] == cls:
                        return m

        return matches[0]
