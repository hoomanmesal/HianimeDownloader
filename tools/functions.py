import os
import time


def get_conformation(prompt: str) -> bool:
    ans: str = input(prompt).lower()
    if ans == "y" or ans == "yes" or ans == "true":
        return True
    elif ans == "n" or ans == "no" or ans == "false":
        return False
    else:
        print("Please provide a valid response")
        return get_conformation(prompt)


def get_int_in_range(
    prompt: str, _min: int = 0, _max: int | float = float("inf"), default: int | None = None
) -> int:
    ans: str = input(prompt)
    if not ans and default is not None:
        return default
    try:
        _int: int = int(ans)
    except ValueError:
        print("Invalid input. Please provide a valid number.")
        return get_int_in_range(prompt, _min, _max, default)

    if _min <= _int <= _max:
        return _int

    print("Invalid input. The provide input was not within the expected range.")
    return get_int_in_range(prompt, _min, _max, default)


def safe_remove(file: str, retries: int = 5, delay: int = 2):
    for _ in range(retries):
        try:
            if os.path.exists(file):
                os.remove(file)
                return
            print("No file exists")
            return
        except PermissionError:
            print("Retrying deletion of files")
            time.sleep(delay)
    print("failed to remove file")


def play_error_sound():
    try:
        import winsound
        # A simple "unhappy" melody with small pauses to ensure notes are distinct
        winsound.Beep(440, 200)   # A4
        time.sleep(0.05)
        winsound.Beep(349, 200)   # F4
        time.sleep(0.05)
        winsound.Beep(261, 500)   # C4
    except ImportError:
        # Not on Windows, or winsound not available
        print("\a")  # System bell
    except Exception:
        pass
