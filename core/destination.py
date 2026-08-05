from pathlib import Path


def validate_and_get_destination_path():

    while True:

        destination = input("\nEnter destination path\n> ").strip().strip('"')

        if destination == "":
            print("Destination path cannot be empty.")
            continue

        dest_path = Path(destination)

        # Case B: Entire path exists
        if dest_path.exists():
            return dest_path

        # Case A: Leaf directory does not exist, but parent exists
        if dest_path.parent.exists():
            print("\nFolder does not exist.\n")
            choice = input("Would you like to create it?\n(Y/N): ").strip().lower()

            if choice in ("y", "yes"):
                dest_path.mkdir(exist_ok=True)
                print("\nFolder created successfully.")
                return dest_path
            else:
                print("\nIncorrect folder location.")
                continue

        # Case C: Parent directory does not exist
        print("\nParent directory does not exist.\nPlease enter a valid location.")
        continue
