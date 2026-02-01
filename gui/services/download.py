"""Download service that wraps extractors for GUI use."""

import requests
from dataclasses import dataclass
from queue import Queue
from threading import Thread, Event as ThreadEvent
from typing import Any, Literal, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from gui.services.events import Event, EventEmitter, EventType
from gui.services.extractor_adapter import GUIHianimeExtractor, GUIDownloadConfig
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
        self._extractor: Optional[GUIHianimeExtractor] = None
        self.title_trans = str.maketrans("", "", "".join(self.BAD_TITLE_CHARS))

        # Subtitle selection synchronization
        self._subtitle_event = ThreadEvent()
        self._subtitle_options: Optional[list[str]] = None
        self._subtitle_selection: Optional[str] = None

        # Retry prompt synchronization
        self._retry_event = ThreadEvent()
        self._retry_message: Optional[str] = None
        self._retry_result: Optional[Literal["retry", "skip", "abort"]] = None

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
                except Exception:
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

    def _subtitle_selection_callback(self, subtitles: list[str]) -> Optional[str]:
        """
        Callback for subtitle selection.

        This is called from the background thread when multiple subtitles are found.
        It emits an event and waits for the GUI to respond via set_subtitle_selection().
        """
        if not subtitles:
            return None

        if len(subtitles) == 1:
            return subtitles[0]

        # Reset the event and store options
        self._subtitle_event.clear()
        self._subtitle_options = subtitles
        self._subtitle_selection = None

        # Emit event to notify GUI to show dialog
        self._emit(EventType.SUBTITLE_CHOICE_NEEDED, {
            "subtitles": subtitles,
        })

        self._emit(EventType.LOG_MESSAGE, {
            "message": f"Multiple subtitles found ({len(subtitles)}), waiting for selection...",
            "level": "INFO",
        })

        # Wait for GUI to set the selection (with timeout)
        self._subtitle_event.wait(timeout=120)  # 2 minute timeout

        result = self._subtitle_selection
        self._subtitle_options = None
        self._subtitle_selection = None

        if result:
            self._emit(EventType.LOG_MESSAGE, {
                "message": "Subtitle selected",
                "level": "INFO",
            })
        else:
            self._emit(EventType.LOG_MESSAGE, {
                "message": "No subtitle selected, skipping",
                "level": "WARN",
            })

        return result

    def set_subtitle_selection(self, selection: Optional[str]):
        """
        Set the subtitle selection from the GUI.

        This should be called by the GUI after the user makes a selection in the dialog.
        """
        self._subtitle_selection = selection
        self._subtitle_event.set()

    def _retry_callback(self, message: str) -> bool:
        """
        Callback for retry prompts.

        This is called from the background thread when an error occurs and retry is possible.
        It emits an event and waits for the GUI to respond via set_retry_result().

        Returns:
            True to retry, False to skip
        """
        # Reset the event and store message
        self._retry_event.clear()
        self._retry_message = message
        self._retry_result = None

        # Emit event to notify GUI to show dialog
        self._emit(EventType.RETRY_PROMPT, {
            "message": message,
        })

        self._emit(EventType.LOG_MESSAGE, {
            "message": f"Error: {message} - waiting for user decision...",
            "level": "WARN",
        })

        # Wait for GUI to set the result (with timeout)
        self._retry_event.wait(timeout=300)  # 5 minute timeout

        result = self._retry_result
        self._retry_message = None
        self._retry_result = None

        if result == "retry":
            self._emit(EventType.LOG_MESSAGE, {"message": "Retrying...", "level": "INFO"})
            return True
        elif result == "abort":
            self._emit(EventType.LOG_MESSAGE, {"message": "Aborting download", "level": "WARN"})
            self.cancel()
            return False
        else:  # skip
            self._emit(EventType.LOG_MESSAGE, {"message": "Skipping...", "level": "INFO"})
            return False

    def set_retry_result(self, result: Literal["retry", "skip", "abort"]):
        """
        Set the retry result from the GUI.

        This should be called by the GUI after the user makes a decision in the error dialog.
        """
        self._retry_result = result
        self._retry_event.set()

    def _download_worker(self, config: DownloadConfig):
        """Background worker for download operation using GUIHianimeExtractor."""
        try:
            self._emit(EventType.DOWNLOAD_START, {
                "anime": config.anime.name,
                "episodes": f"{config.options.start_episode}-{config.options.end_episode}",
            })
            self._emit(EventType.LOG_MESSAGE, {
                "message": f"Starting download: {config.anime.name}",
                "level": "INFO",
            })

            # Create extractor-specific event emitter that routes to our queue
            extractor_events = EventEmitter()

            # Forward all events from extractor to our queue
            for event_type in EventType:
                extractor_events.on(event_type, lambda data, et=event_type: self._emit(et, data))

            # Create the GUI extractor adapter
            self._extractor = GUIHianimeExtractor(
                events=extractor_events,
                subtitle_callback=self._subtitle_selection_callback,
                retry_callback=self._retry_callback,
            )

            # Build the download config for the extractor
            extractor_config = GUIDownloadConfig(
                anime_url=config.anime.url,
                anime_name=config.anime.name,
                sub_episodes=config.anime.sub_episodes,
                dub_episodes=config.anime.dub_episodes,
                download_type=config.options.download_type,
                server=config.options.server,
                season=config.options.season,
                start_episode=config.options.start_episode,
                end_episode=config.options.end_episode,
                output_dir=config.options.output_dir,
                download_subtitles=config.options.download_subtitles,
                use_aria=config.options.use_aria,
            )

            # Run the download
            results = self._extractor.download(extractor_config)

            # Summarize results
            successful = sum(1 for r in results if r.success)
            failed = sum(1 for r in results if not r.success)
            skipped = sum(1 for r in results if r.already_exists)

            self._emit(EventType.DOWNLOAD_COMPLETE, {
                "anime": config.anime.name,
                "total": len(results),
                "successful": successful,
                "failed": failed,
                "skipped": skipped,
            })

            summary = f"Download complete: {successful} successful"
            if skipped > 0:
                summary += f", {skipped} skipped"
            if failed > 0:
                summary += f", {failed} failed"

            self._emit(EventType.LOG_MESSAGE, {"message": summary, "level": "OK"})

        except Exception as e:
            self._emit(EventType.DOWNLOAD_ERROR, {"error": str(e)})
            self._emit(EventType.LOG_MESSAGE, {"message": f"Download error: {e}", "level": "ERROR"})
        finally:
            self._extractor = None
            self._is_running = False

    def cancel(self):
        """Cancel the current operation."""
        if self._extractor:
            self._extractor.cancel()
        self._is_running = False
        self._emit(EventType.LOG_MESSAGE, {"message": "Operation cancelled", "level": "WARN"})

    @property
    def is_running(self) -> bool:
        """Check if a background operation is currently running."""
        return self._is_running
