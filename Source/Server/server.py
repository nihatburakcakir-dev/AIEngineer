from http.server import BaseHTTPRequestHandler, HTTPServer
import json

from Source.Brain.brain import Brain
from Source.Knowledge.importer import Importer

brain = Brain()
importer = Importer()


class Handler(BaseHTTPRequestHandler):

    def do_POST(self):

        length = int(
            self.headers["Content-Length"]
        )

        body = self.rfile.read(
            length
        ).decode("utf-8")

        data = json.loads(body)

        if "objects" in data:

            importer.import_scene(
                data["objects"]
            )

        print("=" * 60)
        print("UNITY REQUEST")
        print("=" * 60)
        print(
            json.dumps(
                data,
                indent=4,
                ensure_ascii=False
            )
        )

        tasks = brain.think(
            data["prompt"]
        )

        response = {

            "workflow":"AI Workflow",

            "tasks":[

                {

                    "action":t.action,

                    "target":t.target

                }

                for t in tasks

            ]

        }

        response_json = json.dumps(
            response,
            ensure_ascii=False
        )

        self.send_response(200)

        self.send_header(
            "Content-Type",
            "application/json"
        )

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


if __name__=="__main__":

    run()
