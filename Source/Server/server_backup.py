from http.server import BaseHTTPRequestHandler, HTTPServer
import json

from Source.Brain.brain import Brain
from Source.Executor.executor import Executor, Command
from Source.Validator.validator import Validator

brain = Brain()
executor = Executor()
validator = Validator()


class Handler(BaseHTTPRequestHandler):

    def do_POST(self):

        length = int(self.headers["Content-Length"])
        body = self.rfile.read(length).decode("utf-8")

        data = json.loads(body)

        print("=" * 60)
        print("UNITY DATA")
        print("=" * 60)
        print(json.dumps(data, indent=4, ensure_ascii=False))

        action = brain.understand(
            text=data["prompt"],
        context=data
        )

        print()
        print("AI ACTION")
        print("=" * 60)
        print(action)

        command = Command(
            action=action.action,
            target=action.target,
            effect=action.effect or ""
        )

        command = validator.validate(
            command,
            data
        )

        executor.execute(command)

        response = {
            "action": command.action,
            "target": command.target,
            "effect": command.effect
        }

        response_json = json.dumps(response)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        self.wfile.write(
            response_json.encode("utf-8")
        )


def run():

    server = HTTPServer(
        ("127.0.0.1",8080),
        Handler
    )

    print("Server running...")

    server.serve_forever()


if __name__ == "__main__":
    run()



