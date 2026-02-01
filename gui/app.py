"""Main GUI application window."""

import customtkinter as ctk
from typing import Any

from gui.frames.search import SearchFrame
from gui.frames.results import ResultsFrame, AnimeResult
from gui.frames.options import OptionsFrame
from gui.frames.progress import ProgressFrame
from gui.frames.logs import LogFrame
from gui.services.download import DownloadService, DownloadConfig
from gui.services.events import EventType
from tools.config import load_config


class HianimeGUI(ctk.CTk):
    """Main application window for HiAnime Downloader."""

    def __init__(self):
        super().__init__()

        # Load configuration
        self.config = load_config()

        # Window setup
        self.title("HiAnime Downloader")
        self.geometry("750x700")
        self.minsize(650, 600)

        # Set appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Initialize services
        self.download_service = DownloadService(self)
        self._setup_event_handlers()

        # Create UI components
        self._create_widgets()

    def _setup_event_handlers(self):
        """Set up event handlers for download service events."""
        events = self.download_service.events

        # Search events
        events.on(EventType.SEARCH_START, self._on_search_start)
        events.on(EventType.SEARCH_COMPLETE, self._on_search_complete)
        events.on(EventType.SEARCH_ERROR, self._on_search_error)

        # Download events
        events.on(EventType.DOWNLOAD_START, self._on_download_start)
        events.on(EventType.DOWNLOAD_PROGRESS, self._on_download_progress)
        events.on(EventType.DOWNLOAD_COMPLETE, self._on_download_complete)
        events.on(EventType.DOWNLOAD_ERROR, self._on_download_error)

        # Episode events
        events.on(EventType.EPISODE_START, self._on_episode_start)
        events.on(EventType.EPISODE_COMPLETE, self._on_episode_complete)

        # Capture events
        events.on(EventType.CAPTURE_START, self._on_capture_start)
        events.on(EventType.CAPTURE_PROGRESS, self._on_capture_progress)
        events.on(EventType.CAPTURE_COMPLETE, self._on_capture_complete)

        # Status events
        events.on(EventType.STATUS_UPDATE, self._on_status_update)
        events.on(EventType.LOG_MESSAGE, self._on_log_message)

    def _create_widgets(self):
        """Create and layout all UI components."""
        # Main container with padding
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=15, pady=15)

        # Search frame
        self.search_frame = SearchFrame(
            main_container,
            on_search=self._on_search,
        )
        self.search_frame.pack(fill="x", pady=(0, 10))

        # Results frame
        self.results_frame = ResultsFrame(
            main_container,
            on_select=self._on_anime_selected,
        )
        self.results_frame.pack(fill="x", pady=(0, 10))

        # Options frame
        default_output = self.config.get("output_dir", "output")
        self.options_frame = OptionsFrame(
            main_container,
            default_output_dir=default_output,
        )
        self.options_frame.pack(fill="x", pady=(0, 10))

        # Apply config defaults
        hianime_config = self.config.get("hianime", {})
        if "type" in hianime_config:
            self.options_frame.type_var.set(hianime_config["type"])
        if "server" in hianime_config:
            self.options_frame.server_var.set(hianime_config["server"])
        if self.config.get("aria", False):
            self.options_frame.aria_var.set(True)
        if self.config.get("no_subtitles", False):
            self.options_frame.subtitles_var.set(False)

        # Button container
        btn_container = ctk.CTkFrame(main_container, fg_color="transparent")
        btn_container.pack(fill="x", pady=(0, 10))

        # Download button
        self.download_btn = ctk.CTkButton(
            btn_container,
            text="Start Download",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._on_download,
        )
        self.download_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # Cancel button
        self.cancel_btn = ctk.CTkButton(
            btn_container,
            text="Cancel",
            height=40,
            width=100,
            font=ctk.CTkFont(size=14),
            fg_color="#8B0000",
            hover_color="#A52A2A",
            state="disabled",
            command=self._on_cancel,
        )
        self.cancel_btn.pack(side="right")

        # Progress frame
        self.progress_frame = ProgressFrame(main_container)
        self.progress_frame.pack(fill="x", pady=(0, 10))

        # Log frame (expandable)
        self.log_frame = LogFrame(main_container)
        self.log_frame.pack(fill="both", expand=True)

        # Initial log message
        self.log_frame.log_info("HiAnime Downloader ready")

    def _on_search(self, query: str):
        """Handle search request."""
        self.download_service.search(query)

    def _on_anime_selected(self, anime: AnimeResult):
        """Handle anime selection."""
        self.options_frame.set_anime(anime)
        self.log_frame.log_info(f"Selected: {anime.name}")

    def _on_download(self):
        """Handle download button click."""
        # Validate selection
        anime = self.results_frame.get_selected()
        if not anime:
            self.log_frame.log_warning("Please select an anime first")
            return

        options = self.options_frame.get_options()
        if not options:
            self.log_frame.log_error("Invalid options")
            return

        # Validate episode range
        max_episodes = anime.sub_episodes if options.download_type == "sub" else anime.dub_episodes
        if max_episodes == 0:
            self.log_frame.log_error(f"No {options.download_type} episodes available for this anime")
            return

        if options.start_episode < 1 or options.end_episode > max_episodes:
            self.log_frame.log_error(f"Episode range must be between 1 and {max_episodes}")
            return

        if options.start_episode > options.end_episode:
            self.log_frame.log_error("Start episode cannot be greater than end episode")
            return

        # Start download
        config = DownloadConfig(anime=anime, options=options)
        self.download_service.download(config)

    def _on_cancel(self):
        """Handle cancel button click."""
        self.download_service.cancel()
        self.cancel_btn.configure(state="disabled")

    # Event handlers

    def _on_search_start(self, data: dict[str, Any]):
        """Handle search start event."""
        self.search_frame.set_loading(True)
        self.results_frame.clear()

    def _on_search_complete(self, data: dict[str, Any]):
        """Handle search complete event."""
        self.search_frame.set_loading(False)
        results = data.get("results", [])
        self.results_frame.display_results(results)

    def _on_search_error(self, data: dict[str, Any]):
        """Handle search error event."""
        self.search_frame.set_loading(False)
        self.log_frame.log_error(f"Search failed: {data.get('error', 'Unknown error')}")

    def _on_download_start(self, data: dict[str, Any]):
        """Handle download start event."""
        self.download_btn.configure(state="disabled", text="Downloading...")
        self.cancel_btn.configure(state="normal")
        self.search_frame.set_loading(True)
        self.options_frame.set_enabled(False)
        self.progress_frame.reset()

    def _on_download_progress(self, data: dict[str, Any]):
        """Handle download progress event."""
        percent = data.get("percent", 0)
        speed = data.get("speed", "")
        eta = data.get("eta", "")

        self.progress_frame.set_progress(percent)
        if speed or eta:
            self.progress_frame.set_details(f"{speed}  |  ETA: {eta}")

    def _on_download_complete(self, data: dict[str, Any]):
        """Handle download complete event."""
        self.download_btn.configure(state="normal", text="Start Download")
        self.cancel_btn.configure(state="disabled")
        self.search_frame.set_loading(False)
        self.options_frame.set_enabled(True)
        self.progress_frame.set_status("Download complete!")
        self.progress_frame.set_progress(1.0)
        self.progress_frame.set_indeterminate(False)

    def _on_download_error(self, data: dict[str, Any]):
        """Handle download error event."""
        self.download_btn.configure(state="normal", text="Start Download")
        self.cancel_btn.configure(state="disabled")
        self.search_frame.set_loading(False)
        self.options_frame.set_enabled(True)
        self.progress_frame.set_status("Error occurred")
        self.progress_frame.set_indeterminate(False)

    def _on_episode_start(self, data: dict[str, Any]):
        """Handle episode start event."""
        episode = data.get("episode", 0)
        current = data.get("current", 0)
        total = data.get("total", 0)
        self.progress_frame.set_status(f"Episode {episode} ({current}/{total})")
        self.progress_frame.set_progress(0)

    def _on_episode_complete(self, data: dict[str, Any]):
        """Handle episode complete event."""
        current = data.get("current", 0)
        total = data.get("total", 0)
        # Update overall progress based on completed episodes
        if total > 0:
            overall_progress = current / total
            self.progress_frame.set_progress(overall_progress)

    def _on_capture_start(self, data: dict[str, Any]):
        """Handle capture start event."""
        episode = data.get("episode", 0)
        self.progress_frame.set_status(f"Capturing Episode {episode}...")
        self.progress_frame.set_indeterminate(True)

    def _on_capture_progress(self, data: dict[str, Any]):
        """Handle capture progress event."""
        attempt = data.get("attempt", 0)
        max_attempts = data.get("max_attempts", 45)
        found_video = data.get("found_video", False)
        found_subtitle = data.get("found_subtitle", False)

        status_parts = [f"Capturing... ({attempt}/{max_attempts})"]
        if found_video:
            status_parts.append("[Video OK]")
        if found_subtitle:
            status_parts.append("[Subtitle OK]")

        self.progress_frame.set_details(" ".join(status_parts))

    def _on_capture_complete(self, data: dict[str, Any]):
        """Handle capture complete event."""
        self.progress_frame.set_indeterminate(False)
        self.progress_frame.set_details("")

    def _on_status_update(self, data: dict[str, Any]):
        """Handle status update event."""
        status = data.get("status", "")
        if status:
            self.progress_frame.set_status(status)

    def _on_log_message(self, data: dict[str, Any]):
        """Handle log message event."""
        message = data.get("message", "")
        level = data.get("level", "INFO")

        if level == "ERROR":
            self.log_frame.log_error(message)
        elif level == "WARN":
            self.log_frame.log_warning(message)
        elif level == "OK":
            self.log_frame.log_success(message)
        else:
            self.log_frame.log_info(message)


def main():
    """Entry point for the GUI application."""
    app = HianimeGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
