"""Download service that wraps extractors for GUI use."""

import os
import requests
from argparse import Namespace
from dataclasses import dataclass
from queue import Queue
from threading import Thread
from typing import Any, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from gui.services.events import Event, EventEmitter, EventType
from gui.frames.results import AnimeResult
from gui.frames.options import DownloadOptions


@dataclass
class DownloadConfig:
    """Complete configuration for a download operation."""

    anime: AnimeResult
    options: DownloadOptions


class DownloadService:
    """Service for handling search and download operations in background threads."""

    HEADERS: dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.3",
        "Accept-Encoding": "none",
        "Accept-Language": "en-US,en;q=0.8",
        "Connection": "keep-alive",
    }
    URL: str = "https://hianime.to"
    BAD_TITLE_CHARS: list[str] = [
        "-", ".", "/", "\\", "?", "%", "*", "<", ">", "|", '"', "[", "]", ":"
    ]

    def __init__(self, app):
        """Initialize the download service.

        Args:
            app: The main GUI application instance (for thread-safe UI updates)
        """
        self.app = app
        self.events = EventEmitter()
        self.message_queue: Queue[tuple[EventType, dict[str, Any]]] = Queue()
        self._is_running = False
        self._current_thread: Optional[Thread] = None
        self.title_trans = str.maketrans("", "", "".join(self.BAD_TITLE_CHARS))

        # Start queue polling
        self._poll_queue()

    def _poll_queue(self):
        """Poll message queue and dispatch events on main thread."""
        while not self.message_queue.empty():
            event_type, data = self.message_queue.get()
            self.events.emit(Event(event_type, data))

        # Schedule next poll
        self.app.after(100, self._poll_queue)

    def _emit(self, event_type: EventType, data: dict[str, Any] = None):
        """Thread-safe event emission via queue."""
        self.message_queue.put((event_type, data or {}))

    def search(self, query: str):
        """Search for anime in a background thread.

        Args:
            query: The anime name to search for
        """
        if self._is_running:
            return

        self._is_running = True
        self._current_thread = Thread(target=self._search_worker, args=(query,), daemon=True)
        self._current_thread.start()

    def _search_worker(self, query: str):
        """Background worker for search operation."""
        try:
            self._emit(EventType.SEARCH_START, {"query": query})
            self._emit(EventType.LOG_MESSAGE, {"message": f"Searching for: {query}", "level": "INFO"})

            # Perform search
            url = urljoin(self.URL, "/search?keyword=" + query)
            response = requests.get(url, headers=self.HEADERS, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            main_content: Tag = soup.find("div", id="main-content")  # type: ignore

            if not main_content:
                self._emit(EventType.SEARCH_COMPLETE, {"results": [], "query": query})
                self._emit(EventType.LOG_MESSAGE, {"message": "No results found", "level": "WARN"})
                return

            anime_elements: list[Tag] = main_content.find_all("div", class_="flw-item")  # type: ignore

            if not anime_elements:
                self._emit(EventType.SEARCH_COMPLETE, {"results": [], "query": query})
                self._emit(EventType.LOG_MESSAGE, {"message": "No results found", "level": "WARN"})
                return

            # Parse results
            results: list[AnimeResult] = []
            for element in anime_elements:
                try:
                    raw_name: str = element.find("h3", class_="film-name").text  # type: ignore
                    name = raw_name.translate(self.title_trans)
                    url_of_anime = urljoin(
                        self.URL,
                        str(element.find("a", class_="film-poster-ahref item-qtip")["href"]),  # type: ignore
                    )

                    # Get episode counts (may not exist for some anime)
                    try:
                        sub_episodes = int(element.find("div", class_="tick-item tick-sub").text)  # type: ignore
                    except (AttributeError, ValueError):
                        sub_episodes = 0

                    try:
                        dub_episodes = int(element.find("div", class_="tick-item tick-dub").text)  # type: ignore
                    except (AttributeError, ValueError):
                        dub_episodes = 0

                    results.append(AnimeResult(
                        name=name,
                        url=url_of_anime,
                        sub_episodes=sub_episodes,
                        dub_episodes=dub_episodes,
                    ))
                except Exception as e:
                    # Skip malformed entries
                    continue

            self._emit(EventType.SEARCH_COMPLETE, {"results": results, "query": query})
            self._emit(EventType.LOG_MESSAGE, {"message": f"Found {len(results)} results", "level": "INFO"})

        except requests.RequestException as e:
            self._emit(EventType.SEARCH_ERROR, {"error": str(e), "query": query})
            self._emit(EventType.LOG_MESSAGE, {"message": f"Search failed: {e}", "level": "ERROR"})
        except Exception as e:
            self._emit(EventType.SEARCH_ERROR, {"error": str(e), "query": query})
            self._emit(EventType.LOG_MESSAGE, {"message": f"Search error: {e}", "level": "ERROR"})
        finally:
            self._is_running = False

    def download(self, config: DownloadConfig):
        """Start download in a background thread.

        Args:
            config: The download configuration
        """
        if self._is_running:
            return

        self._is_running = True
        self._current_thread = Thread(target=self._download_worker, args=(config,), daemon=True)
        self._current_thread.start()

    def _download_worker(self, config: DownloadConfig):
        """Background worker for download operation.

        This is a placeholder that will be expanded to integrate with
        the actual HianimeExtractor download functionality.
        """
        try:
            self._emit(EventType.DOWNLOAD_START, {
                "anime": config.anime.name,
                "episodes": f"{config.options.start_episode}-{config.options.end_episode}",
            })
            self._emit(EventType.LOG_MESSAGE, {
                "message": f"Starting download: {config.anime.name}",
                "level": "INFO",
            })

            # Build args namespace for extractor
            args = Namespace(
                link=config.anime.url,
                output_dir=config.options.output_dir,
                type=config.options.download_type,
                server=config.options.server,
                aria=config.options.use_aria,
                no_subtitles=not config.options.download_subtitles,
                filename=None,
            )

            # For now, emit a placeholder message
            # Full integration with HianimeExtractor will require refactoring
            # the extractor to support callbacks instead of print statements
            self._emit(EventType.LOG_MESSAGE, {
                "message": "Download service initialized. Full extractor integration pending.",
                "level": "INFO",
            })

            total_episodes = config.options.end_episode - config.options.start_episode + 1
            for i, ep_num in enumerate(range(config.options.start_episode, config.options.end_episode + 1), 1):
                self._emit(EventType.EPISODE_START, {
                    "episode": ep_num,
                    "current": i,
                    "total": total_episodes,
                })
                self._emit(EventType.STATUS_UPDATE, {
                    "status": f"Episode {ep_num} ({i}/{total_episodes})",
                })

                # Placeholder progress simulation
                # In real implementation, this would call extractor methods
                import time
                for progress in range(0, 101, 10):
                    self._emit(EventType.DOWNLOAD_PROGRESS, {
                        "percent": progress / 100,
                        "speed": "-- MB/s",
                        "eta": "--:--",
                    })
                    time.sleep(0.1)

                self._emit(EventType.EPISODE_COMPLETE, {
                    "episode": ep_num,
                    "current": i,
                    "total": total_episodes,
                })
                self._emit(EventType.LOG_MESSAGE, {
                    "message": f"Episode {ep_num} complete (simulated)",
                    "level": "OK",
                })

            self._emit(EventType.DOWNLOAD_COMPLETE, {
                "anime": config.anime.name,
                "total_episodes": total_episodes,
            })
            self._emit(EventType.LOG_MESSAGE, {
                "message": "Download complete!",
                "level": "OK",
            })

        except Exception as e:
            self._emit(EventType.DOWNLOAD_ERROR, {"error": str(e)})
            self._emit(EventType.LOG_MESSAGE, {"message": f"Download error: {e}", "level": "ERROR"})
        finally:
            self._is_running = False

    def cancel(self):
        """Cancel the current operation."""
        # TODO: Implement proper cancellation
        self._is_running = False
        self._emit(EventType.LOG_MESSAGE, {"message": "Operation cancelled", "level": "WARN"})

    @property
    def is_running(self) -> bool:
        """Check if a background operation is currently running."""
        return self._is_running
