"""Error and confirmation dialogs."""

import customtkinter as ctk
from typing import Optional, Literal


class ErrorDialog(ctk.CTkToplevel):
    """Dialog for displaying errors with retry/skip/abort options."""

    def __init__(
        self,
        parent,
        message: str,
        title: str = "Error",
        can_retry: bool = True,
        can_skip: bool = True,
    ):
        super().__init__(parent)
        self.title(title)
        self.result: Optional[Literal["retry", "skip", "abort"]] = None

        # Configure dialog
        self.geometry("450x200")
        self.resizable(False, False)
        self.transient(parent)

        self._create_widgets(message, can_retry, can_skip)

        # Make modal
        self.grab_set()
        self.focus_set()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _create_widgets(self, message: str, can_retry: bool, can_skip: bool):
        """Create dialog widgets."""
        # Error icon and message
        msg_frame = ctk.CTkFrame(self, fg_color="transparent")
        msg_frame.pack(fill="both", expand=True, padx=20, pady=20)

        label = ctk.CTkLabel(
            msg_frame,
            text=message,
            wraplength=400,
            justify="left",
        )
        label.pack(expand=True)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))

        abort_btn = ctk.CTkButton(
            btn_frame,
            text="Abort",
            width=100,
            fg_color="#8B0000",
            hover_color="#A52A2A",
            command=lambda: self._close("abort"),
        )
        abort_btn.pack(side="left")

        if can_skip:
            skip_btn = ctk.CTkButton(
                btn_frame,
                text="Skip",
                width=100,
                fg_color="#555555",
                hover_color="#666666",
                command=lambda: self._close("skip"),
            )
            skip_btn.pack(side="left", padx=10)

        if can_retry:
            retry_btn = ctk.CTkButton(
                btn_frame,
                text="Retry",
                width=100,
                command=lambda: self._close("retry"),
            )
            retry_btn.pack(side="right")

    def _close(self, result: Literal["retry", "skip", "abort"]):
        """Close dialog with result."""
        self.result = result
        self.destroy()

    def get_result(self) -> Optional[Literal["retry", "skip", "abort"]]:
        """Wait for dialog and return result."""
        self.wait_window()
        return self.result


class ConfirmDialog(ctk.CTkToplevel):
    """Simple confirmation dialog."""

    def __init__(
        self,
        parent,
        message: str,
        title: str = "Confirm",
        yes_text: str = "Yes",
        no_text: str = "No",
    ):
        super().__init__(parent)
        self.title(title)
        self.result: Optional[bool] = None

        # Configure dialog
        self.geometry("400x150")
        self.resizable(False, False)
        self.transient(parent)

        self._create_widgets(message, yes_text, no_text)

        # Make modal
        self.grab_set()
        self.focus_set()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _create_widgets(self, message: str, yes_text: str, no_text: str):
        """Create dialog widgets."""
        # Message
        label = ctk.CTkLabel(
            self,
            text=message,
            wraplength=350,
        )
        label.pack(expand=True, padx=20, pady=20)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))

        no_btn = ctk.CTkButton(
            btn_frame,
            text=no_text,
            width=100,
            fg_color="#555555",
            hover_color="#666666",
            command=lambda: self._close(False),
        )
        no_btn.pack(side="left")

        yes_btn = ctk.CTkButton(
            btn_frame,
            text=yes_text,
            width=100,
            command=lambda: self._close(True),
        )
        yes_btn.pack(side="right")

    def _close(self, result: bool):
        """Close dialog with result."""
        self.result = result
        self.destroy()

    def get_result(self) -> Optional[bool]:
        """Wait for dialog and return result."""
        self.wait_window()
        return self.result
