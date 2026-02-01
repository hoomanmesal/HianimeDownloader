"""Progress frame component."""

import customtkinter as ctk


class ProgressFrame(ctk.CTkFrame):
    """Frame displaying download progress."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._create_widgets()

    def _create_widgets(self):
        """Create and layout widgets."""
        # Header
        header = ctk.CTkLabel(
            self,
            text="Progress",
            font=ctk.CTkFont(weight="bold"),
            anchor="w",
        )
        header.pack(fill="x", padx=10, pady=(10, 5))

        # Status label
        self.status_label = ctk.CTkLabel(
            self,
            text="Ready",
            anchor="w",
        )
        self.status_label.pack(fill="x", padx=10, pady=(0, 5))

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 5))
        self.progress_bar.set(0)

        # Details label (speed, ETA)
        self.details_label = ctk.CTkLabel(
            self,
            text="",
            anchor="w",
            text_color="gray",
        )
        self.details_label.pack(fill="x", padx=10, pady=(0, 10))

    def set_status(self, status: str):
        """Set the status text."""
        self.status_label.configure(text=status)

    def set_progress(self, value: float):
        """Set progress bar value (0.0 to 1.0)."""
        self.progress_bar.set(max(0.0, min(1.0, value)))

    def set_details(self, details: str):
        """Set the details text (speed, ETA, etc.)."""
        self.details_label.configure(text=details)

    def reset(self):
        """Reset to initial state."""
        self.status_label.configure(text="Ready")
        self.progress_bar.set(0)
        self.details_label.configure(text="")

    def set_indeterminate(self, indeterminate: bool):
        """Set progress bar to indeterminate mode."""
        if indeterminate:
            self.progress_bar.configure(mode="indeterminate")
            self.progress_bar.start()
        else:
            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate")
