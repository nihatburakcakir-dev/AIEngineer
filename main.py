from Source.Brain.brain import Brain


def main():

    brain = Brain()

    action = brain.understand(
        "Kurdun agzina mavi ates efekti ekle."
    )

    print(action)


if __name__ == "__main__":
    main()
