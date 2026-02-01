import argparse
import os
import time

from colorama import Fore

from extractors.general import GeneralExtractor
from extractors.hianime import HianimeExtractor
from extractors.instagram import InstagramExtractor
from tools.config import load_config, load_session
from tools.functions import play_error_sound


class Main:
    def __init__(self):
        self.args = self.parse_args()
        if getattr(self.args, "last", False):
            session = load_session()
            if session:
                # Override arguments with last session data
                for key, value in session.get("args", {}).items():
                    if getattr(self.args, key, None) is None or key in ["link", "filename", "server", "download_type"]:
                        setattr(self.args, key, value)
                # Store extra session info (like episode range) in args for extractors
                self.args.session_info = session.get("info", {})
            else:
                print(f"{Fore.LIGHTRED_EX}No previous session found.")

        extractor = self.get_extractor()
        extractor.run()

    def get_extractor(self):
        if not self.args.link and not self.args.filename:
            os.system("cls" if os.name == "nt" else "clear")
            ans = input(
                f"{Fore.LIGHTGREEN_EX}GDown {Fore.LIGHTCYAN_EX}Downloader\n\nProvide a link or search for an anime:\n{Fore.LIGHTYELLOW_EX}"
            )
            if "http" in ans.lower():
                self.args.link = ans
            else:
                return HianimeExtractor(args=self.args, name=ans)

        if not self.args.link and self.args.filename:
            return HianimeExtractor(args=self.args, name=self.args.filename)

        if "hianime" in self.args.link:
            return HianimeExtractor(args=self.args)
        if "instagram.com" in self.args.link:
            return InstagramExtractor(args=self.args)
        return GeneralExtractor(args=self.args)

    def parse_args(self):
        config = load_config()
        parser = argparse.ArgumentParser(description="Anime downloader options")

        parser.add_argument(
            "--no-subtitles",
            action="store_true",
            default=config.get("no_subtitles", False),
            help="Skip downloading subtitle files (.vtt)",
        )

        parser.add_argument(
            "-o",
            "--output-dir",
            type=str,
            default=config.get("output_dir", "output"),
            help="Directory to save downloaded files",
        )

        parser.add_argument(
            "-n",
            "--filename",
            type=str,
            default="",
            help="Used for name of anime, or name of output file when using other extractor",
        )

        parser.add_argument(
            "--aria",
            action="store_true",
            default=config.get("aria", False),
            help="Use aria2c as external downloader",
        )

        parser.add_argument(
            "-l",
            "--link",
            type=str,
            default=None,
            help="Provide link to desired content",
        )

        parser.add_argument(
            "-t",
            "--type",
            type=str,
            dest="download_type",
            default=config.get("hianime", {}).get("type", "sub"),
            choices=["sub", "dub", "s", "d"],
            help="Download type (sub or dub)",
        )

        parser.add_argument(
            "--server",
            type=str,
            default=config.get("hianime", {}).get("server"),
            help="Streaming Server to download from",
        )

        parser.add_argument(
            "--last",
            action="store_true",
            help="Repeat the last download session",
        )

        return parser.parse_args()


if __name__ == "__main__":
    start = time.time()
    try:
        Main()
    except Exception as e:
        play_error_sound()
        raise e
    elapsed = time.time() - start
    print(f"Took {int(elapsed / 60)}:{int((elapsed % 60))} to finish")
