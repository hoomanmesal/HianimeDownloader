"""Log frame component."""

import customtkinter as ctk
from datetime import datetime


class LogFrame(ctk.CTkFrame):
    """Frame displaying activity logs."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._create_widgets()

    def _create_widgets(self):
        """Create and layout widgets."""
        # Header with clear button
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        header = ctk.CTkLabel(
            header_frame,
            text="Activity Log",
            font=ctk.CTkFont(weight="bold"),
            anchor="w",
        )
        header.pack(side="left")

        clear_btn = ctk.CTkButton(
            header_frame,
            text="Clear",
            width=60,
            height=24,
            command=self.clear,
        )
        clear_btn.pack(side="right")

        # Log textbox
        self.log_textbox = ctk.CTkTextbox(self, height=120)
        self.log_textbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.log_textbox.configure(state="disabled")

    def log(self, message: str, level: str = "INFO"):
        """Add a log message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] [{level}] {message}\n"

        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", formatted)
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def log_info(self, message: str):
        """Log an info message."""
        self.log(message, "INFO")

    def log_error(self, message: str):
        """Log an error message."""
        self.log(message, "ERROR")

    def log_warning(self, message: str):
        """Log a warning message."""
        self.log(message, "WARN")

    def log_success(self, message: str):
        """Log a success message."""
        self.log(message, "OK")

    def clear(self):
        """Clear all log messages."""
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")
