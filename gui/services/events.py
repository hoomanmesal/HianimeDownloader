"""Event system for GUI communication with background services."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable


class EventType(Enum):
    """Types of events that can be emitted by services."""

    # Search events
    SEARCH_START = auto()
    SEARCH_COMPLETE = auto()
    SEARCH_ERROR = auto()

    # Capture events (getting stream URLs)
    CAPTURE_START = auto()
    CAPTURE_PROGRESS = auto()
    CAPTURE_COMPLETE = auto()

    # Download events
    DOWNLOAD_START = auto()
    DOWNLOAD_PROGRESS = auto()
    DOWNLOAD_COMPLETE = auto()
    DOWNLOAD_ERROR = auto()

    # Episode events
    EPISODE_START = auto()
    EPISODE_COMPLETE = auto()
    EPISODE_ERROR = auto()

    # User interaction events
    SUBTITLE_CHOICE_NEEDED = auto()
    RETRY_PROMPT = auto()

    # General
    LOG_MESSAGE = auto()
    STATUS_UPDATE = auto()


@dataclass
class Event:
    """An event with type and associated data."""

    type: EventType
    data: dict[str, Any] = field(default_factory=dict)


class EventEmitter:
    """Simple event emitter for pub/sub pattern."""

    def __init__(self):
        self._listeners: dict[EventType, list[Callable[[dict[str, Any]], None]]] = {}

    def on(self, event_type: EventType, callback: Callable[[dict[str, Any]], None]) -> None:
        """Register a callback for an event type."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)

    def off(self, event_type: EventType, callback: Callable[[dict[str, Any]], None]) -> None:
        """Unregister a callback for an event type."""
        if event_type in self._listeners:
            self._listeners[event_type] = [cb for cb in self._listeners[event_type] if cb != callback]

    def emit(self, event: Event) -> None:
        """Emit an event to all registered listeners."""
        for callback in self._listeners.get(event.type, []):
            try:
                callback(event.data)
            except Exception as e:
                print(f"Error in event listener for {event.type}: {e}")

    def clear(self) -> None:
        """Clear all listeners."""
        self._listeners.clear()
