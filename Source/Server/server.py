from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import sys

try:
    sys.stdout.reconfigure(
        encoding="utf-8"
    )

    sys.stderr.reconfigure(
        encoding="utf-8"
    )

except Exception:
    pass

from Source.Brain.brain import Brain
from Source.Knowledge.importer import Importer
from Source.Project.importer import ProjectImporter

brain = Brain()

importer = Importer()

project_importer = ProjectImporter()


class Handler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):

        # BaseHTTPRequestHandler writes successful access logs to stderr by
        # default. Unity interprets stderr as an error, so route HTTP access
        # information to stdout and reserve stderr for real exceptions.
        print("[HTTP] " + (format % args))

    def do_POST(self):

        try:

            length = int(
                self.headers["Content-Length"]
            )

            body = self.rfile.read(
                length
            ).decode(
                "utf-8"
            )

            data = json.loads(
                body
            )

            if "objects" in data:

                importer.import_scene(
                    data["objects"]
                )

            if "project" in data:

                project_importer.import_project(
                    data["project"]
                )

            print("=" * 60)
            print("UNITY REQUEST")
            print("=" * 60)

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
                "application/json; charset=utf-8"
            )

            self.end_headers()

            self.wfile.write(
                response_json.encode(
                    "utf-8"
                )
            )

        except Exception as e:

            import traceback

            traceback.print_exc()

            self.send_response(500)

            self.send_header(
                "Content-Type",
                "text/plain"
            )

            self.end_headers()

            self.wfile.write(

                str(e).encode(
                    "utf-8",
                    "ignore"
                )

            )


def run():

    server = HTTPServer(

        ("127.0.0.1",8080),

        Handler

    )

    print()

    print("=" * 60)
    print("AI ENGINE SERVER")
    print("=" * 60)
    print("Listening : http://127.0.0.1:8080")
    print()

    server.serve_forever()


if __name__=="__main__":

    run()
