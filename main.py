from Source.Brain.brain import Brain


def main():

    brain = Brain()

    tasks = brain.think(

        "Kurdun ağzına mavi ateş efekti ekle."

    )

    print()

    print("=" * 60)

    print("TASKS")

    print("=" * 60)

    for t in tasks:

        print(

            t.action,

            t.target

        )


if __name__ == "__main__":

    main()
