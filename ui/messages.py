HEADER_BANNER = "=" * 60 + "\nGitHub Repository Cloner\n" + "=" * 60

READY_PROMPT_BANNER = (
    "\n------------------------------------------\n"
    "Ready for another repository.\n"
    "(Type 'exit' to quit.)\n"
    "------------------------------------------"
)

GOODBYE_MESSAGE = "\nThanks for using Repo_Clone_System!\nGoodbye."


def print_header():
    print(HEADER_BANNER)


def print_ready_banner():
    print(READY_PROMPT_BANNER)


def print_goodbye():
    print(GOODBYE_MESSAGE)
