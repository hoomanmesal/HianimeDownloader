"""Results frame component."""

import customtkinter as ctk
from dataclasses import dataclass
from typing import Optional


@dataclass
class AnimeResult:
    """Represents an anime search result."""

    name: str
    url: str
    sub_episodes: int
    dub_episodes: int


class ResultsFrame(ctk.CTkFrame):
    """Frame displaying anime search results as selectable items."""

    def __init__(self, master, on_select: callable = None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_select_callback = on_select
        self.results: list[AnimeResult] = []
        self.selected_var = ctk.StringVar(value="")

        self._create_widgets()

    def _create_widgets(self):
        """Create and layout widgets."""
        # Header
        header = ctk.CTkLabel(
            self,
            text="Search Results",
            font=ctk.CTkFont(weight="bold"),
            anchor="w",
        )
        header.pack(fill="x", padx=10, pady=(10, 5))

        # Scrollable frame for results
        self.results_container = ctk.CTkScrollableFrame(self, height=150)
        self.results_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Placeholder text
        self.placeholder = ctk.CTkLabel(
            self.results_container,
            text="Search for an anime to see results",
            text_color="gray",
        )
        self.placeholder.pack(pady=20)

    def display_results(self, results: list[AnimeResult]):
        """Display search results."""
        self.results = results
        self.selected_var.set("")

        # Clear existing
        for widget in self.results_container.winfo_children():
            widget.destroy()

        if not results:
            self.placeholder = ctk.CTkLabel(
                self.results_container,
                text="No results found",
                text_color="gray",
            )
            self.placeholder.pack(pady=20)
            return

        # Add results as radio buttons
        for result in results:
            text = f"{result.name}  (Sub: {result.sub_episodes}, Dub: {result.dub_episodes})"
            rb = ctk.CTkRadioButton(
                self.results_container,
                text=text,
                variable=self.selected_var,
                value=result.url,
                command=self._on_selection_change,
            )
            rb.pack(anchor="w", pady=3)

    def _on_selection_change(self):
        """Handle selection change."""
        selected = self.get_selected()
        if selected and self.on_select_callback:
            self.on_select_callback(selected)

    def get_selected(self) -> Optional[AnimeResult]:
        """Get the currently selected anime result."""
        selected_url = self.selected_var.get()
        if not selected_url:
            return None
        for result in self.results:
            if result.url == selected_url:
                return result
        return None

    def clear(self):
        """Clear all results."""
        self.results = []
        self.selected_var.set("")
        for widget in self.results_container.winfo_children():
            widget.destroy()
        self.placeholder = ctk.CTkLabel(
            self.results_container,
            text="Search for an anime to see results",
            text_color="gray",
        )
        self.placeholder.pack(pady=20)
