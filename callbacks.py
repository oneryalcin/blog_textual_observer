from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Optional, Any
import logging
from pathlib import Path
from textual.app import App

class ChatEvent(Enum):
    START_PROCESSING = "start_processing"
    THINKING = "thinking"
    PROCESSING_COMPLETE = "processing_complete"
    ERROR = "error"

class ChatCallback(ABC):
    """Abstract base class for chat callbacks."""
    
    @abstractmethod
    def on_event(self, event: ChatEvent, message: str) -> None:
        """Handle chat events."""
        pass

class FileLogCallback(ChatCallback):
    """Callback that logs events to a file."""
    
    def __init__(self, log_file: str = "events.log") -> None:
        self.logger = logging.getLogger("ChatEvents")
        self.logger.setLevel(logging.INFO)
        
        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)

    def on_event(self, event: ChatEvent, message: str) -> None:
        self.logger.info(f"Event: {event.value} - Message: {message}")

class TuiCallback(ChatCallback):
    """Callback that updates the TUI interface."""
    
    def __init__(self, app: App, message_container, create_message_func) -> None:
        self.app = app
        self.message_container = message_container
        self.create_message = create_message_func

    def on_event(self, event: ChatEvent, message: str) -> None:
        def update_ui() -> None:
            if event == ChatEvent.START_PROCESSING:
                self.message_container.mount(self.create_message("Event", f"🤔 Processing your message: {message}"))
            elif event == ChatEvent.THINKING:
                self.message_container.mount(self.create_message("Event", f"💭 {message}"))
            elif event == ChatEvent.ERROR:
                self.message_container.mount(self.create_message("Event", f"❌ Error: {message}"))
            elif event == ChatEvent.PROCESSING_COMPLETE:
                self.message_container.mount(self.create_message("Event", f"✅ Response ready: {message}"))
            
            # Ensure the message container scrolls to show new messages
            self.message_container.scroll_end(animate=False)
            # Force a refresh of the screen
            self.message_container.refresh()

        # Call the UI update from the main thread
        """
        This pattern is essential because:
        - Bot processing happens in background threads
        - UI updates must be thread-safe
        - Prevents race conditions and UI corruption
        - Maintains responsiveness of the application
        
        The call_from_thread method essentially queues the UI update to be executed safely on the main thread, where all UI operations should occur.
        
        Key Reasons:
        - Thread Confinement: Most GUI frameworks (including Textual) are not thread-safe
        - Single Thread Model: UI operations must happen on the main thread
        - Race Conditions: Direct updates from background threads can corrupt UI state
        """
        self.app.call_from_thread(update_ui)