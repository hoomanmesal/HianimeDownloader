"""Options frame component."""

import customtkinter as ctk
from tkinter import filedialog
from dataclasses import dataclass
from typing import Optional

from gui.frames.results import AnimeResult


@dataclass
class DownloadOptions:
    """Download configuration options."""

    download_type: str  # "sub" or "dub"
    server: str
    season: int
    start_episode: int
    end_episode: int
    output_dir: str
    download_subtitles: bool
    use_aria: bool
    download_all: bool


class OptionsFrame(ctk.CTkFrame):
    """Frame containing download configuration options."""

    def __init__(self, master, default_output_dir: str = "output", **kwargs):
        super().__init__(master, **kwargs)
        self.default_output_dir = default_output_dir
        self.current_anime: Optional[AnimeResult] = None

        self._create_widgets()

    def _create_widgets(self):
        """Create and layout widgets."""
        # Header
        header = ctk.CTkLabel(
            self,
            text="Download Options",
            font=ctk.CTkFont(weight="bold"),
            anchor="w",
        )
        header.pack(fill="x", padx=10, pady=(10, 5))

        # Options container
        options_container = ctk.CTkFrame(self, fg_color="transparent")
        options_container.pack(fill="x", padx=10, pady=5)

        # Row 1: Type and Server
        row1 = ctk.CTkFrame(options_container, fg_color="transparent")
        row1.pack(fill="x", pady=5)

        ctk.CTkLabel(row1, text="Type:").pack(side="left", padx=(0, 5))
        self.type_var = ctk.StringVar(value="sub")
        self.type_menu = ctk.CTkOptionMenu(
            row1,
            values=["sub", "dub"],
            variable=self.type_var,
            width=100,
            command=self._on_type_change,
        )
        self.type_menu.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(row1, text="Server:").pack(side="left", padx=(0, 5))
        self.server_var = ctk.StringVar(value="HD-2")
        self.server_menu = ctk.CTkOptionMenu(
            row1,
            values=["HD-1", "HD-2"],
            variable=self.server_var,
            width=100,
        )
        self.server_menu.pack(side="left")

        # Row 2: Season and Episodes
        row2 = ctk.CTkFrame(options_container, fg_color="transparent")
        row2.pack(fill="x", pady=5)

        ctk.CTkLabel(row2, text="Season:").pack(side="left", padx=(0, 5))
        self.season_entry = ctk.CTkEntry(row2, width=60)
        self.season_entry.insert(0, "1")
        self.season_entry.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(row2, text="Episodes:").pack(side="left", padx=(0, 5))
        self.start_ep_entry = ctk.CTkEntry(row2, width=60, placeholder_text="from")
        self.start_ep_entry.pack(side="left", padx=(0, 5))
        ctk.CTkLabel(row2, text="to").pack(side="left", padx=5)
        self.end_ep_entry = ctk.CTkEntry(row2, width=60, placeholder_text="to")
        self.end_ep_entry.pack(side="left")

        # Row 3: Download All checkbox
        row3 = ctk.CTkFrame(options_container, fg_color="transparent")
        row3.pack(fill="x", pady=5)

        self.download_all_var = ctk.BooleanVar(value=False)
        self.download_all_cb = ctk.CTkCheckBox(
            row3,
            text="Download all available episodes",
            variable=self.download_all_var,
            command=self._on_download_all_change,
        )
        self.download_all_cb.pack(side="left")

        # Row 4: Output directory
        row4 = ctk.CTkFrame(options_container, fg_color="transparent")
        row4.pack(fill="x", pady=5)

        ctk.CTkLabel(row4, text="Output:").pack(side="left", padx=(0, 5))
        self.output_entry = ctk.CTkEntry(row4)
        self.output_entry.insert(0, self.default_output_dir)
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.browse_btn = ctk.CTkButton(
            row4,
            text="Browse",
            width=80,
            command=self._browse_output,
        )
        self.browse_btn.pack(side="right")

        # Row 5: Additional options
        row5 = ctk.CTkFrame(options_container, fg_color="transparent")
        row5.pack(fill="x", pady=5)

        self.subtitles_var = ctk.BooleanVar(value=True)
        self.subtitles_cb = ctk.CTkCheckBox(
            row5,
            text="Download Subtitles",
            variable=self.subtitles_var,
        )
        self.subtitles_cb.pack(side="left", padx=(0, 20))

        self.aria_var = ctk.BooleanVar(value=False)
        self.aria_cb = ctk.CTkCheckBox(
            row5,
            text="Use Aria2c",
            variable=self.aria_var,
        )
        self.aria_cb.pack(side="left")

    def _browse_output(self):
        """Open directory browser."""
        directory = filedialog.askdirectory(initialdir=self.output_entry.get())
        if directory:
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, directory)

    def _on_download_all_change(self):
        """Handle download all checkbox change."""
        if self.download_all_var.get() and self.current_anime:
            self._update_episode_range_for_all()
            self.start_ep_entry.configure(state="disabled")
            self.end_ep_entry.configure(state="disabled")
        else:
            self.start_ep_entry.configure(state="normal")
            self.end_ep_entry.configure(state="normal")

    def _on_type_change(self, value: str):
        """Handle type change to update episode count if download all is checked."""
        if self.download_all_var.get() and self.current_anime:
            self._update_episode_range_for_all()

    def _update_episode_range_for_all(self):
        """Update episode range based on current anime and type selection."""
        if not self.current_anime:
            return

        download_type = self.type_var.get()
        if download_type == "sub":
            max_ep = self.current_anime.sub_episodes
        else:
            max_ep = self.current_anime.dub_episodes

        self.start_ep_entry.configure(state="normal")
        self.end_ep_entry.configure(state="normal")
        self.start_ep_entry.delete(0, "end")
        self.start_ep_entry.insert(0, "1")
        self.end_ep_entry.delete(0, "end")
        self.end_ep_entry.insert(0, str(max_ep))
        self.start_ep_entry.configure(state="disabled")
        self.end_ep_entry.configure(state="disabled")

    def set_anime(self, anime: Optional[AnimeResult]):
        """Set the current anime and update UI accordingly."""
        self.current_anime = anime
        if anime and self.download_all_var.get():
            self._update_episode_range_for_all()

    def get_options(self) -> Optional[DownloadOptions]:
        """Get current download options."""
        try:
            season = int(self.season_entry.get() or "1")
            start_ep = int(self.start_ep_entry.get() or "1")
            end_ep = int(self.end_ep_entry.get() or "1")
        except ValueError:
            return None

        return DownloadOptions(
            download_type=self.type_var.get(),
            server=self.server_var.get(),
            season=season,
            start_episode=start_ep,
            end_episode=end_ep,
            output_dir=self.output_entry.get(),
            download_subtitles=self.subtitles_var.get(),
            use_aria=self.aria_var.get(),
            download_all=self.download_all_var.get(),
        )

    def set_enabled(self, enabled: bool):
        """Enable or disable all inputs."""
        state = "normal" if enabled else "disabled"
        self.type_menu.configure(state=state)
        self.server_menu.configure(state=state)
        self.season_entry.configure(state=state)
        self.download_all_cb.configure(state=state)
        self.browse_btn.configure(state=state)
        self.subtitles_cb.configure(state=state)
        self.aria_cb.configure(state=state)

        # Episode entries depend on download_all state
        if enabled and not self.download_all_var.get():
            self.start_ep_entry.configure(state="normal")
            self.end_ep_entry.configure(state="normal")
        else:
            self.start_ep_entry.configure(state="disabled")
            self.end_ep_entry.configure(state="disabled")
