"""Search frame component."""

import customtkinter as ctk


class SearchFrame(ctk.CTkFrame):
    """Frame containing the anime search input and button."""

    def __init__(self, master, on_search: callable = None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_search_callback = on_search

        self._create_widgets()

    def _create_widgets(self):
        """Create and layout widgets."""
        # Search entry
        self.search_entry = ctk.CTkEntry(
            self,
            placeholder_text="Enter anime name...",
            height=36,
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda e: self._on_search())

        # Search button
        self.search_btn = ctk.CTkButton(
            self,
            text="Search",
            width=100,
            height=36,
            command=self._on_search,
        )
        self.search_btn.pack(side="right")

    def _on_search(self):
        """Handle search button click."""
        query = self.search_entry.get().strip()
        if query and self.on_search_callback:
            self.on_search_callback(query)

    def set_loading(self, loading: bool):
        """Set loading state."""
        if loading:
            self.search_btn.configure(state="disabled", text="Searching...")
        else:
            self.search_btn.configure(state="normal", text="Search")

    def get_query(self) -> str:
        """Get the current search query."""
        return self.search_entry.get().strip()
