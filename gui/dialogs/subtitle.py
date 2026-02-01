"""Subtitle selection dialog."""

import customtkinter as ctk
from typing import Optional


class SubtitleDialog(ctk.CTkToplevel):
    """Dialog for selecting from multiple subtitle options."""

    def __init__(self, parent, subtitles: list[str], title: str = "Select Subtitle"):
        super().__init__(parent)
        self.title(title)
        self.selected: Optional[str] = None

        # Configure dialog
        self.geometry("400x300")
        self.resizable(False, False)
        self.transient(parent)

        self._create_widgets(subtitles)

        # Make modal
        self.grab_set()
        self.focus_set()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _create_widgets(self, subtitles: list[str]):
        """Create dialog widgets."""
        # Label
        label = ctk.CTkLabel(
            self,
            text="Multiple subtitles found. Please select one:",
            wraplength=350,
        )
        label.pack(pady=(20, 10), padx=20)

        # Scrollable frame for options
        scroll_frame = ctk.CTkScrollableFrame(self, height=150)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Radio buttons
        self.var = ctk.StringVar(value=subtitles[0] if subtitles else "")
        for sub in subtitles:
            rb = ctk.CTkRadioButton(
                scroll_frame,
                text=sub,
                variable=self.var,
                value=sub,
            )
            rb.pack(anchor="w", pady=3)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=100,
            command=self._on_cancel,
        )
        cancel_btn.pack(side="left")

        select_btn = ctk.CTkButton(
            btn_frame,
            text="Select",
            width=100,
            command=self._on_select,
        )
        select_btn.pack(side="right")

    def _on_select(self):
        """Handle select button."""
        self.selected = self.var.get()
        self.destroy()

    def _on_cancel(self):
        """Handle cancel button."""
        self.selected = None
        self.destroy()

    def get_result(self) -> Optional[str]:
        """Wait for dialog and return selected subtitle."""
        self.wait_window()
        return self.selected
