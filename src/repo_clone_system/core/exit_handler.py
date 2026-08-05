import sys


def handle_keyboard_interrupt():
    print("\n--------------------------------------------------\n")
    print("Operation cancelled by user.")
    print("\nThank you for using Repo_Clone_System!")
    print("Goodbye 👋\n")
    print("--------------------------------------------------")
    sys.exit(0)


def handle_eof_error():
    print("\nInput stream closed.")
    print("Exiting Repo_Clone_System...")
    sys.exit(0)


def run_with_exit_handler(main_func):
    """Executes the main function wrapped in global interruption handlers."""
    try:
        main_func()
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except EOFError:
        handle_eof_error()
