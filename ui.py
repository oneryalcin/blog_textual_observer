"""
A Text User Interface (TUI) chat application built with the Textual framework.
This module implements a chat interface that allows users to interact with a chatbot
in a terminal-based environment. It features real-time message display, background 
processing, and event logging.

Key components:
- ChatMessage: Custom widget for displaying formatted chat messages
- ChatInterface: Main application class handling the UI and bot interactions
- Background processing: Asynchronous message handling to keep UI responsive
"""

from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer, Container
from textual.widgets import Header, Input, Label
from textual.binding import Binding
from textual.worker import Worker, WorkerState
from rich.text import Text
from datetime import datetime
from pathlib import Path

from bot import SimpleBot
from callbacks import TuiCallback, FileLogCallback

class ChatMessage(Label):
    """
    A custom widget for displaying chat messages with formatting.
    
    Each message shows:
    - The sender's name in bold
    - A timestamp
    - The message content
    
    Args:
        sender (str): Name of the message sender
        message (str): Content of the message
    """
    
    def __init__(self, sender: str, message: str) -> None:
        # Format timestamp as HH:MM:SS
        current_time = datetime.now().strftime("%H:%M:%S")
        # Create rich text with markup for styling
        formatted_message = Text.from_markup(
            f"[bold]{sender}[/bold] ({current_time})\n{message}"
        )
        super().__init__(formatted_message)

class ChatInterface(App):
    """
    Main TUI application class implementing the chat interface.
    
    Features:
    - Real-time message display
    - Background message processing
    - Keyboard shortcuts
    - Event logging
    - Scrollable message history
    
    The interface is styled using CSS defined in static/styles.css
    """

    # Path to CSS file for styling the interface
    CSS_PATH = Path(__file__).parent / "static" / "styles.css"

    # Define keyboard shortcuts
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+c", "quit", "Quit", show=False),
    ]

    def __init__(self) -> None:
        """Initialize the chat interface with a SimpleBot instance."""
        super().__init__()
        self.bot = SimpleBot()

    def on_mount(self) -> None:
        """
        Set up callbacks after the app is mounted.
        
        Initializes:
        1. TUI callback for updating the interface
        2. File logging callback for event tracking
        
        
        Timing:
        - on_mount is called after all widgets are created and mounted
        - It's safe to query and reference widgets here
        - Perfect place for post-initialization setup
        
        Widget Access:
        - query_one("#message-container") works here because widgets exist
        - Would fail if called in __init__ (widgets don't exist yet)
        
        Lifecycle Order:
        - Textual App Lifecycle
            1. __init__()           # Initial setup
            2. compose()           # Create widgets
            3. on_mount()         # Post-mount setup
            4. on_ready()        # App ready for user interaction
        
        Best Practices:
        - Use __init__ for basic initialization
        - Use compose for widget creation
        - Use on_mount for:
            - Widget queries
            - Event handlers setup
            - Callback registration
            - Post-initialization configuration
        
        This method is crucial for proper initialization timing in Textual applications, ensuring all components are properly set up after the UI is ready.
        """
        message_container = self.query_one("#message-container")
        
        # Add TUI callback to handle bot events and update the interface
        tui_callback = TuiCallback(self, message_container, ChatMessage)
        self.bot.add_callback(tui_callback)
        
        # Set up file logging for events
        log_path = Path(__file__).parent / "events.log"
        file_callback = FileLogCallback(str(log_path))
        self.bot.add_callback(file_callback)

    def compose(self) -> ComposeResult:
        """
        Create and arrange the UI widgets.
        
        Layout:
        - Header at the top
        - Chat container with:
            - Scrollable message history
            - Input field at the bottom
        """
        yield Header()
        with Container(id="chat-container"):
            with ScrollableContainer(id="message-container"):
                # Display initial welcome message
                yield ChatMessage("Bot", "Hello! How can I help you today?")
            with Container(id="input-container"):
                yield Input(placeholder="Type your message here and press Enter...", id="user-input")

    
    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Handle worker state changes.
        
        Args:
            event (Worker.StateChanged): The worker state change event
        
        Notes:
        1. on_worker_state_changed is a Textual event handler (main thread)
        2. Direct UI updates are safe in the main thread
        3. Worker state changes provide a reliable way to handle completion
        
        This pattern follows Textual's thread safety model:
        - Event handlers → Direct UI updates
        - Background operations → Use call_from_thread
        - Worker state changes → Already in main thread
        
        """
        message_container = self.query_one("#message-container")
        
        if event.worker.name == "bot_processing":  # Only handle our bot worker
            if event.worker.state == WorkerState.SUCCESS:
                # We're already in the main thread, so update UI directly
                result = event.worker.result
                message_container.mount(ChatMessage("Bot", result))
                message_container.scroll_end(animate=False)


    def process_message_in_background(self, user_input: str) -> Worker:
        """Process user messages in a background thread to keep UI responsive.
        
        Args:
            user_input (str): The message from the user
            
        Returns:
            Worker: A background worker processing the message
        """
        message_container = self.query_one("#message-container")
        message_container.mount(ChatMessage("You", user_input))
        message_container.scroll_end(animate=False)
        
        # Create worker for background processing
        worker = self.run_worker(
            lambda: self.bot.process_message(user_input),
            name="bot_processing",  # Important for identifying our worker
            thread=True
        )
        return worker


    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """
        Handle user input submission when Enter is pressed.
        
        Args:
            event (Input.Submitted): The input submission event
        """
        user_input = event.value
        if not user_input.strip():
            return

        # Clear input field after submission
        input_widget = self.query_one("#user-input", Input)
        input_widget.value = ""

        # Process message asynchronously
        self.process_message_in_background(user_input)

if __name__ == "__main__":
    app = ChatInterface()
    app.run()
