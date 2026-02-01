import sys

from colorama import Fore


class YTDLogger:
    def __init__(self):
        self.has_errors = False
        self.fragment_errors = False

    def debug(self, msg: str):
        if not msg.startswith("[download]"):
            return
        
        if "fragment not found" in msg.lower() or "error" in msg.lower():
            self.has_errors = True
            if "fragment" in msg.lower():
                self.fragment_errors = True

        color = (
            Fore.LIGHTRED_EX
            if "fragment not found" in msg
            else (Fore.YELLOW + "\n" if "error" in msg else Fore.LIGHTCYAN_EX)
        )
        new_msg = f"{color}[YT-DLP] {msg[11:]}"
        if "ETA" in msg:
            sys.stdout.write(f"\r{new_msg}")
            sys.stdout.flush()
            return
        elif "100% of" in msg:
            sys.stdout.write(f"\r{new_msg}\n")
            sys.stdout.flush()
            return
        print(new_msg)

    def info(self, msg):
        print(f"[Logger Info] {msg}")

    def warning(self, msg):
        if "fragment" in msg.lower() or "error" in msg.lower():
            self.has_errors = True
            if "fragment" in msg.lower():
                self.fragment_errors = True

    def error(self, msg):
        self.has_errors = True
        if "fragment" in msg.lower():
            self.fragment_errors = True
        print(f"{Fore.LIGHTRED_EX}[Logger Error] {msg}")


