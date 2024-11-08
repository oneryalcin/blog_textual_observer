import random
import time
from typing import Dict, List, Optional
from callbacks import ChatCallback, ChatEvent

class SimpleBot:
    """A simple synchronous chatbot that generates random responses with event callbacks."""
    
    def __init__(self) -> None:
        self.callbacks: List[ChatCallback] = []
        self.responses: Dict[str, List[str]] = {
            "greeting": [
                "Hello! How can I assist you today?",
                "Hi there! What's on your mind?",
                "Greetings! How may I help you?"
            ],
            "default": [
                "Interesting point! Let me think about that...",
                "I understand what you're saying. Here's what I think...",
                "That's a good question. From my perspective...",
                "Let me process that for a moment..."
            ],
            "farewell": [
                "Goodbye! Have a great day!",
                "See you later! Take care!",
                "Bye for now! Feel free to come back anytime!"
            ]
        }
        self.thinking_messages = [
            "Analyzing your message...",
            "Processing that information...",
            "Considering the best response...",
            "Computing an appropriate reply..."
        ]

    def add_callback(self, callback: ChatCallback) -> None:
        """Add a callback to the bot."""
        self.callbacks.append(callback)

    def notify_callbacks(self, event: ChatEvent, message: str) -> None:
        """Notify all callbacks of an event."""
        for callback in self.callbacks:
            callback.on_event(event, message)

    def process_message(self, message: str) -> str:
        """Process the user message and return a response with event notifications."""
        try:
            self.notify_callbacks(ChatEvent.START_PROCESSING, "Starting to process message")
            
            message = message.lower().strip()
            
            # Simulate longer processing with multiple thinking steps
            time.sleep(random.uniform(0.5, 5.0))
            self.notify_callbacks(ChatEvent.THINKING, random.choice(self.thinking_messages))
            
            time.sleep(random.uniform(0.5, 3.0))
            self.notify_callbacks(ChatEvent.THINKING, "Analyzing sentiment...")
            
            # Determine response type
            if any(word in message for word in ["hello", "hi", "hey", "greetings"]):
                response = random.choice(self.responses["greeting"])
            elif any(word in message for word in ["bye", "goodbye", "see you", "farewell"]):
                response = random.choice(self.responses["farewell"])
            else:
                response = random.choice(self.responses["default"])
            
            time.sleep(random.uniform(0.5, 1.0))
            self.notify_callbacks(ChatEvent.THINKING, f"Debug: Generated response: {response}")
            self.notify_callbacks(ChatEvent.PROCESSING_COMPLETE, f"Debug: About to return: {response}")
        
            return response
            
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            self.notify_callbacks(ChatEvent.ERROR, error_message)
            return "I apologize, but I encountered an error while processing your message." 