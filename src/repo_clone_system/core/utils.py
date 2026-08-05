import subprocess


def check_git():
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        return True

    except Exception:
        return False


def get_repo_name(url):
    url = url.rstrip("/")

    if url.endswith(".git"):
        url = url[:-4]

    return url.split("/")[-1]
