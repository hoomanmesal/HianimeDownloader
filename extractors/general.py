import os
from colorama import Fore
from yt_dlp import YoutubeDL
from tools.functions import get_conformation



class GeneralExtractor:
    def __init__(self, args):
        self.args = args

    def run(self):
        status = self.yt_dlp_download(
            self.args.link,
            self.args.output_dir,
            (
                self.args.filename
                if self.args.filename
                else input("Enter a file name for the file: ")
            ),
        )
        
        print(f"\n{Fore.LIGHTCYAN_EX}=== Download Summary ===")
        if status['success']:
            print(f"{Fore.LIGHTGREEN_EX}Successfully downloaded.")
        elif status.get('fragment_error'):
            print(f"{Fore.LIGHTRED_EX}Download was INCOMPLETE (Fragments missing).")
            if get_conformation(f"{Fore.LIGHTCYAN_EX}Would you like to delete the incomplete file and try redownloading it? (y/n): "):
                location = self.args.output_dir
                name = self.args.filename or "" # Should have been set in run or input
                filepath = location + os.sep + name + ".mp4"
                from tools.functions import safe_remove
                safe_remove(filepath)
                self.run() # Recursive retry
        else:
            print(f"{Fore.LIGHTRED_EX}Download FAILED ({status.get('error', 'Unknown error')}).")

    @staticmethod
    def yt_dlp_download(url: str, location: str, name: str) -> dict:
        from tools.YTDLogger import YTDLogger
        logger = YTDLogger()
        os.makedirs(location, exist_ok=True)
        yt_dlp_options = {
            "no_warnings": False,
            "quiet": False,
            "outtmpl": location + os.sep + name + ".mp4",
            "format": "bv*+ba/best",
            "fragment_retries": 10,
            "retries": 10,
            "socket_timeout": 60,
            "sleep_interval_requests": 1,
            "force_keyframes_at_cuts": True,
            "merge_output_format": "mp4",
            "keepvideo": True,
            "logger": logger,
        }

        if os.path.exists("cookies.txt"):
            print("Using local cookies")
            yt_dlp_options["cookies"] = "cookies.txt"

        status = {"success": True, "fragment_error": False, "error": None}
        try:
            with YoutubeDL(yt_dlp_options) as ydl:
                try:
                    ydl.download([url])
                    if logger.fragment_errors:
                        status["success"] = False
                        status["fragment_error"] = True
                except KeyboardInterrupt:
                    print(f"\n{Fore.LIGHTCYAN_EX}Canceling Download...")
                    status["success"] = False
                    status["error"] = "Cancelled"
                except Exception as e:
                    print(f"{Fore.LIGHTRED_EX}yt-dlp error: {e}")
                    status["success"] = False
                    status["error"] = str(e)
        except Exception as e:
            print(f"{Fore.LIGHTRED_EX}Error initializing yt-dlp: {e}")
            status["success"] = False
            status["error"] = str(e)
            
        return status

