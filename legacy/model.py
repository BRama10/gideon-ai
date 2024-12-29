import base64
from typing import List, Dict, Union, Optional
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import os
from datetime import datetime

class Message:
    def __init__(self, role: str = "user"):
        self.role = role
        self.content: List[Dict] = []
        self.timestamp = datetime.now()

    def add_text(self, text: str) -> 'Message':
        """Add text content to the message."""
        self.content.append({
            "type": "text",
            "text": text
        })
        return self

    def add_image(self, image_path: Union[str, Path]) -> 'Message':
        """Add image content to the message using base64 encoding."""
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")
        
        self.content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
        })
        return self
    
    def add_image_base64(self, base64_image: str) -> 'Message':
        """Add image content to the message using pre-encoded base64 data."""
        self.content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
        })
        return self


    def to_dict(self) -> Dict:
        """Convert the message to a dictionary format for API consumption."""
        # For API consumption, we need to flatten the content if it's a single text message
        if len(self.content) == 1 and self.content[0]["type"] == "text":
            return {
                "role": self.role,
                "content": self.content[0]["text"]
            }
        return {
            "role": self.role,
            "content": self.content
        }

class Conversation:
    def __init__(self):
        self.messages: List[Message] = []
        self.id = str(datetime.now().timestamp())
        self.creation_time = datetime.now()
        self.last_updated = datetime.now()

    def add_message(self, message: Message):
        """Add a message to the conversation."""
        self.messages.append(message)
        self.last_updated = datetime.now()

    def get_messages_for_api(self) -> List[Dict]:
        """Get messages in format suitable for API consumption."""
        return [msg.to_dict() for msg in self.messages]

    def get_last_n_messages(self, n: int) -> List[Message]:
        """Get the last n messages from the conversation."""
        return self.messages[-n:] if n > 0 else []

class LLMMessageBuilder:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the message builder.
        If api_key is not provided, it will attempt to load from environment variables.
        """
        load_dotenv()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("API key must be provided either directly or through environment variables")
        
        self.client = OpenAI(api_key=self.api_key)
        self.conversation = Conversation()
        self.model = "gpt-4o"  # default model
        self.current_message: Optional[Message] = None

    def create_message(self, role: str = "user") -> Message:
        """Create and return a new message with the specified role."""
        self.current_message = Message(role)
        return self.current_message

    def set_model(self, model: str) -> 'LLMMessageBuilder':
        """Set the model to be used for completion."""
        self.model = model
        return self

    def clear_conversation(self) -> 'LLMMessageBuilder':
        """Clear the conversation history."""
        self.conversation = Conversation()
        self.current_message = None
        return self

    def get_conversation_history(self) -> List[Message]:
        """Get all messages in the current conversation."""
        return self.conversation.messages

    def get_last_n_messages(self, n: int) -> List[Message]:
        """Get the last n messages from the conversation."""
        return self.conversation.get_last_n_messages(n)

    def send(self, max_tokens: int = 300, include_history: bool = True) -> str:
        """
        Send the messages to the API and get the response.
        Returns the content of the response.
        
        Args:
            max_tokens: Maximum number of tokens in the response
            include_history: Whether to include conversation history in the API call
        """
        if not self.current_message:
            raise ValueError("No current message to send")

        try:
            # Add the current message to the conversation
            self.conversation.add_message(self.current_message)
            
            # Prepare messages for API call
            messages_for_api = (
                self.conversation.get_messages_for_api() if include_history 
                else [self.current_message.to_dict()]
            )

            # Send to API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages_for_api,
                max_tokens=max_tokens
            )

            # Create and store assistant's response message
            assistant_message = Message("assistant")
            assistant_message.add_text(response.choices[0].message.content)
            self.conversation.add_message(assistant_message)

            # Clear current message
            self.current_message = None
            
            return response.choices[0].message.content

        except Exception as e:
            raise Exception(f"Error sending message to API: {str(e)}")

    def save_conversation(self, file_path: str):
        """Save the conversation history to a file."""
        # Basic implementation - could be expanded to use proper serialization
        with open(file_path, 'w') as f:
            for msg in self.conversation.messages:
                f.write(f"Role: {msg.role}\n")
                f.write(f"Time: {msg.timestamp}\n")
                f.write("Content:\n")
                for content in msg.content:
                    if content["type"] == "text":
                        f.write(f"{content['text']}\n")
                    elif content["type"] == "image_url":
                        f.write("[Image content]\n")
                f.write("\n---\n\n")

# Example usage:
if __name__ == "__main__":
    # Initialize the builder
    builder = LLMMessageBuilder()
    
    # First message
    builder.create_message("user") \
        .add_text("Hello! How are you?")
    response1 = builder.send()
    print("First response:", response1)
    
    # Second message with image
    builder.create_message("user") \
        .add_text("What's in this image?") \
        .add_image("/Users/balaji/gideon/temp_photo/frame_11.538.jpg")
    response2 = builder.send()
    print("Second response:", response2)
    
    # Get conversation history
    history = builder.get_conversation_history()
    print(f"\nConversation has {len(history)} messages")
    
    # Save conversation
    builder.save_conversation("conversation_history.txt")