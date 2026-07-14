import argparse
from pathlib import Path


def create_files(base: Path, files: list[str]):

    base.mkdir(parents=True, exist_ok=True)

    for file in files:

        path = base / file

        if not path.exists():

            path.write_text("", encoding="utf-8")

            print(f"[OK] {path}")

        else:

            print(f"[EXISTS] {path}")


def create_module(name: str):

    create_files(
        Path("Source") / name,
        [
            "__init__.py",
            f"{name.lower()}.py",
            "models.py",
            f"test_{name.lower()}.py",
        ]
    )


def create_executor():

    create_files(
        Path("Source") / "Executor",
        [
            "__init__.py",
            "executor.py",
            "commands.py",
            "test_executor.py",
        ]
    )


def main():

    parser = argparse.ArgumentParser()

    sub = parser.add_subparsers(dest="command")

    create = sub.add_parser("create-module")
    create.add_argument("name")

    sub.add_parser("create-executor")

    args = parser.parse_args()

    if args.command == "create-module":

        create_module(args.name)

    elif args.command == "create-executor":

        create_executor()

    else:

        parser.print_help()


if __name__ == "__main__":
    main()
