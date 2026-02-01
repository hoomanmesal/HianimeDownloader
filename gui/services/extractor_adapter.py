"""
GUI-compatible adapter for HianimeExtractor.

This module provides a wrapper around the HianimeExtractor that replaces
interactive prompts with callbacks, making it suitable for GUI integration.
"""

import os
import sys
import time
from argparse import Namespace
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Protocol
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag
from langdetect import detect as detect_lang

from extractors.hianime import Anime, HianimeExtractor
from gui.services.events import Event, EventEmitter, EventType


@dataclass
class GUIDownloadConfig:
    """Complete configuration for a GUI-initiated download."""

    anime_url: str
    anime_name: str
    sub_episodes: int
    dub_episodes: int
    download_type: str  # "sub" or "dub"
    server: str  # "HD-1", "HD-2", etc.
    season: int
    start_episode: int
    end_episode: int
    output_dir: str
    download_subtitles: bool = True
    use_aria: bool = False


@dataclass
class CaptureResult:
    """Result of media capture operation."""

    success: bool
    m3u8: Optional[str] = None
    vtt: Optional[str] = None
    headers: Optional[dict] = None
    vtt_headers: Optional[dict] = None
    all_vtt: list[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class DownloadResult:
    """Result of a single episode download."""

    episode_number: int
    success: bool
    already_exists: bool = False
    fragment_error: bool = False
    subtitle_success: bool = True
    error: Optional[str] = None
    file_path: Optional[str] = None


class SubtitleSelectionCallback(Protocol):
    """Protocol for subtitle selection callback."""

    def __call__(self, subtitles: list[str]) -> Optional[str]:
        """
        Called when multiple subtitles are found.

        Args:
            subtitles: List of subtitle URLs to choose from

        Returns:
            Selected subtitle URL, or None to skip subtitles
        """
        ...


class RetryCallback(Protocol):
    """Protocol for retry confirmation callback."""

    def __call__(self, message: str) -> bool:
        """
        Called when a retry is needed.

        Args:
            message: Description of what failed

        Returns:
            True to retry, False to skip
        """
        ...


class GUIHianimeExtractor:
    """
    GUI-compatible wrapper for HianimeExtractor.

    This class adapts the HianimeExtractor for use with a GUI by:
    - Accepting all configuration upfront
    - Using event emitters for progress reporting
    - Using callbacks for user interaction
    """

    def __init__(
        self,
        events: EventEmitter,
        subtitle_callback: Optional[SubtitleSelectionCallback] = None,
        retry_callback: Optional[RetryCallback] = None,
    ):
        """
        Initialize the GUI extractor adapter.

        Args:
            events: Event emitter for progress updates
            subtitle_callback: Callback for subtitle selection (optional)
            retry_callback: Callback for retry confirmation (optional)
        """
        self.events = events
        self.subtitle_callback = subtitle_callback
        self.retry_callback = retry_callback

        # Extractor constants
        self.HEADERS = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.3",
            "Accept-Encoding": "none",
            "Accept-Language": "en-US,en;q=0.8",
            "Connection": "keep-alive",
        }
        self.URL = "https://hianime.to"
        self.BAD_TITLE_CHARS = ["-", ".", "/", "\\", "?", "%", "*", "<", ">", "|", '"', "[", "]", ":"]
        self.TITLE_TRANS = str.maketrans("", "", "".join(self.BAD_TITLE_CHARS))

        self._cancelled = False
        self._extractor: Optional[HianimeExtractor] = None

    def _emit(self, event_type: EventType, data: dict[str, Any] = None):
        """Emit an event."""
        self.events.emit(Event(event_type, data or {}))

    def _log(self, message: str, level: str = "INFO"):
        """Emit a log message."""
        self._emit(EventType.LOG_MESSAGE, {"message": message, "level": level})

    def cancel(self):
        """Cancel the current operation."""
        self._cancelled = True
        self._log("Cancellation requested...", "WARN")

    def download(self, config: GUIDownloadConfig) -> list[DownloadResult]:
        """
        Download anime episodes using the provided configuration.

        Args:
            config: Complete download configuration

        Returns:
            List of download results for each episode
        """
        self._cancelled = False
        results: list[DownloadResult] = []

        try:
            # Create Anime dataclass
            anime = Anime(
                name=config.anime_name,
                url=config.anime_url,
                sub_episodes=config.sub_episodes,
                dub_episodes=config.dub_episodes,
                download_type=config.download_type,
                season_number=config.season,
            )

            # Create args namespace for the extractor
            args = Namespace(
                link=config.anime_url,
                output_dir=config.output_dir,
                download_type=config.download_type,
                server=config.server,
                aria=config.use_aria,
                no_subtitles=not config.download_subtitles,
                filename=None,
                last=False,
                session_info={},
            )

            # Initialize the underlying extractor
            self._extractor = HianimeExtractor(args)
            self._extractor.selected_server_name = config.server

            # Create output folder
            folder = os.path.join(
                os.path.abspath(config.output_dir),
                f"{anime.name} ({anime.download_type[0].upper()}{anime.download_type[1:]})",
            )
            os.makedirs(folder, exist_ok=True)

            self._log(f"Output folder: {folder}")
            self._emit(EventType.DOWNLOAD_START, {
                "anime": anime.name,
                "folder": folder,
                "total_episodes": config.end_episode - config.start_episode + 1,
            })

            # Configure driver and get episode list
            self._log("Configuring browser...")
            self._extractor.configure_driver()

            self._log(f"Loading anime page: {anime.url}")
            self._extractor.driver.get(anime.url)

            # Select server
            self._log(f"Selecting server: {config.server}")
            self._extractor.select_server(anime.download_type)

            # Get episode URLs
            episode_list = self._extractor.get_episode_urls(
                self._extractor.driver.page_source,
                config.start_episode,
                config.end_episode,
            )

            self._log(f"Found {len(episode_list)} episodes to download")

            # Initialize capture lists
            self._extractor.captured_video_urls = []
            self._extractor.captured_subtitle_urls = []

            total_episodes = len(episode_list)

            # Process each episode
            for idx, episode in enumerate(episode_list, 1):
                if self._cancelled:
                    self._log("Download cancelled by user", "WARN")
                    break

                ep_num = episode["number"]
                ep_title = episode["title"]
                name = f"{anime.name} - s{anime.season_number:02}e{ep_num:02} - {ep_title}"
                filepath = os.path.join(folder, f"{name}.mp4")

                self._emit(EventType.EPISODE_START, {
                    "episode": ep_num,
                    "title": ep_title,
                    "current": idx,
                    "total": total_episodes,
                })
                self._log(f"Processing Episode {ep_num}: {ep_title}")

                # Check if already exists
                if os.path.exists(filepath):
                    self._log(f"Episode {ep_num} already exists, skipping")
                    results.append(DownloadResult(
                        episode_number=ep_num,
                        success=True,
                        already_exists=True,
                        file_path=filepath,
                    ))
                    self._emit(EventType.EPISODE_COMPLETE, {
                        "episode": ep_num,
                        "current": idx,
                        "total": total_episodes,
                        "skipped": True,
                    })
                    continue

                # Capture media URLs
                self._emit(EventType.CAPTURE_START, {"episode": ep_num})
                capture_result = self._capture_episode(episode, anime.download_type, config.download_subtitles)

                if not capture_result.success:
                    self._log(f"Failed to capture Episode {ep_num}: {capture_result.error}", "ERROR")
                    results.append(DownloadResult(
                        episode_number=ep_num,
                        success=False,
                        error=capture_result.error,
                    ))
                    continue

                # Update episode with captured URLs
                episode["m3u8"] = capture_result.m3u8
                episode["headers"] = capture_result.headers
                if capture_result.vtt:
                    episode["vtt"] = capture_result.vtt
                    episode["vtt_headers"] = capture_result.vtt_headers

                self._emit(EventType.CAPTURE_COMPLETE, {"episode": ep_num})

                # Download the episode
                download_result = self._download_episode(anime, episode, folder, config.download_subtitles)
                results.append(download_result)

                self._emit(EventType.EPISODE_COMPLETE, {
                    "episode": ep_num,
                    "current": idx,
                    "total": total_episodes,
                    "success": download_result.success,
                })

                # Small delay between episodes
                if idx < total_episodes:
                    time.sleep(2)

            # Cleanup
            self._cleanup_driver()

            self._emit(EventType.DOWNLOAD_COMPLETE, {
                "anime": anime.name,
                "results": len(results),
                "successful": sum(1 for r in results if r.success),
            })

            return results

        except Exception as e:
            self._log(f"Download failed: {e}", "ERROR")
            self._emit(EventType.DOWNLOAD_ERROR, {"error": str(e)})
            self._cleanup_driver()
            raise

    def _capture_episode(
        self,
        episode: dict,
        download_type: str,
        download_subtitles: bool,
    ) -> CaptureResult:
        """Capture media URLs for an episode."""
        try:
            # Navigate to episode
            self._extractor.driver.requests.clear()
            self._extractor.driver.get(episode["url"])
            self._extractor.select_server(download_type)
            self._extractor.driver.execute_script("window.focus();")

            # Capture media requests
            found_m3u8 = False
            found_vtt = not download_subtitles
            attempt = 0
            max_attempts = 45
            refresh_at = (15, 30)

            urls: dict[str, Any] = {"all_vtt": [], "vtt_headers_map": {}}

            while (not found_m3u8 or not found_vtt) and attempt < max_attempts:
                if self._cancelled:
                    return CaptureResult(success=False, error="Cancelled")

                self._emit(EventType.CAPTURE_PROGRESS, {
                    "attempt": attempt + 1,
                    "max_attempts": max_attempts,
                    "found_video": found_m3u8,
                    "found_subtitle": found_vtt,
                })

                for request in self._extractor.driver.requests:
                    if not request.response:
                        continue

                    uri = request.url.lower()

                    # Check for m3u8
                    if (
                        not found_m3u8
                        and ".m3u8" in uri
                        and "chunklist" not in uri
                        and uri not in self._extractor.captured_video_urls
                    ):
                        urls["m3u8"] = uri
                        urls["headers"] = dict(request.headers)
                        found_m3u8 = True
                        self._log("Found video stream")
                        continue

                    # Check for vtt
                    if (
                        not found_vtt
                        and ".vtt" in uri
                        and "thumbnail" not in uri
                        and uri not in self._extractor.captured_subtitle_urls
                        and uri not in urls["all_vtt"]
                    ):
                        # Check language
                        try:
                            vtt_content = requests.get(uri, headers=dict(request.headers), timeout=10).content.decode("utf-8")
                            if detect_lang(vtt_content) == "en":
                                urls["all_vtt"].append(uri)
                                urls["vtt_headers_map"][uri] = dict(request.headers)
                        except Exception:
                            pass

                attempt += 1

                # Click player to trigger stream
                if attempt > 0 and attempt % 10 == 0:
                    self._extractor.driver.execute_script(
                        "try { document.querySelector('#ani_player')?.click(); } catch(e) {}"
                    )

                # Refresh at certain attempts
                if attempt in refresh_at:
                    self._extractor.driver.refresh()
                    self._extractor.select_server(download_type)

                time.sleep(1)

            if not found_m3u8:
                return CaptureResult(success=False, error="No video stream found")

            # Handle subtitle selection
            vtt_url = None
            vtt_headers = None

            if urls["all_vtt"]:
                if len(urls["all_vtt"]) == 1:
                    vtt_url = urls["all_vtt"][0]
                    vtt_headers = urls["vtt_headers_map"][vtt_url]
                elif self.subtitle_callback:
                    # Ask user to select
                    self._emit(EventType.SUBTITLE_CHOICE_NEEDED, {"subtitles": urls["all_vtt"]})
                    selected = self.subtitle_callback(urls["all_vtt"])
                    if selected and selected in urls["all_vtt"]:
                        vtt_url = selected
                        vtt_headers = urls["vtt_headers_map"][vtt_url]
                else:
                    # Default to first
                    vtt_url = urls["all_vtt"][0]
                    vtt_headers = urls["vtt_headers_map"][vtt_url]

            return CaptureResult(
                success=True,
                m3u8=urls["m3u8"],
                headers=urls["headers"],
                vtt=vtt_url,
                vtt_headers=vtt_headers,
                all_vtt=urls["all_vtt"],
            )

        except Exception as e:
            return CaptureResult(success=False, error=str(e))

    def _download_episode(
        self,
        anime: Anime,
        episode: dict,
        folder: str,
        download_subtitles: bool,
    ) -> DownloadResult:
        """Download a single episode."""
        ep_num = episode["number"]
        name = f"{anime.name} - s{anime.season_number:02}e{ep_num:02} - {episode['title']}"
        filepath = os.path.join(folder, f"{name}.mp4")
        subtitle_path = os.path.join(folder, f"{name}.vtt")

        subtitle_success = True

        # Download subtitles first (they expire faster)
        if download_subtitles and episode.get("vtt"):
            self._log(f"Downloading subtitles for Episode {ep_num}")
            subtitle_success = self._download_subtitle(
                episode["vtt"],
                episode.get("vtt_headers", episode["headers"]),
                subtitle_path,
            )
            if not subtitle_success:
                self._log(f"Subtitle download failed for Episode {ep_num}", "WARN")

        # Resolve video URL
        self._log(f"Resolving video stream for Episode {ep_num}")
        video_url = self._extractor.look_for_variants(episode["m3u8"], episode["headers"])

        if not video_url:
            return DownloadResult(
                episode_number=ep_num,
                success=False,
                error="Could not resolve video URL",
                subtitle_success=subtitle_success,
            )

        # Download video
        self._log(f"Downloading Episode {ep_num}")
        self._emit(EventType.DOWNLOAD_START, {"episode": ep_num, "file": filepath})

        status = self._extractor.yt_dlp_download(video_url, episode["headers"], filepath)

        return DownloadResult(
            episode_number=ep_num,
            success=status["success"],
            fragment_error=status.get("fragment_error", False),
            subtitle_success=subtitle_success,
            error=status.get("error"),
            file_path=filepath if status["success"] else None,
        )

    def _download_subtitle(self, url: str, headers: dict, path: str) -> bool:
        """Download a subtitle file."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=30)
                if response.status_code == 200:
                    with open(path, "wb") as f:
                        f.write(response.content)
                    return True
                self._log(f"Subtitle download HTTP {response.status_code} (attempt {attempt + 1})", "WARN")
            except Exception as e:
                self._log(f"Subtitle download error: {e} (attempt {attempt + 1})", "WARN")

            if attempt < max_retries - 1:
                time.sleep(2)

        return False

    def _cleanup_driver(self):
        """Clean up the browser driver."""
        try:
            if self._extractor and hasattr(self._extractor, "driver"):
                self._extractor.driver.quit()
                delattr(self._extractor, "driver")
        except Exception:
            pass
