import os
import subprocess
import sys


def clone_repo():
    print("=" * 50)
    print("GitHub Repository Cloner")
    print("=" * 50)

    # Get repository URL
    repo_url = input("\nEnter GitHub Repository URL:\n> ").strip()

    if not repo_url:
        print("❌ Repository URL cannot be empty.")
        sys.exit(1)

    # Get destination folder
    destination = input("\nEnter destination folder:\n> ").strip().strip('"')

    if not destination:
        print("❌ Destination cannot be empty.")
        sys.exit(1)

    # Create destination if it doesn't exist
    os.makedirs(destination, exist_ok=True)

    print("\n📥 Cloning repository...\n")

    try:
        subprocess.run(
            ["git", "clone", repo_url],
            cwd=destination,
            check=True
        )

        print("\n✅ Repository cloned successfully!")
        print(f"📁 Location: {destination}")

    except FileNotFoundError:
        print("\n❌ Git is not installed or not found in PATH.")
    except subprocess.CalledProcessError:
        print("\n❌ Failed to clone repository.")
        print("Check the repository URL and your internet connection.")


if __name__ == "__main__":
    clone_repo()