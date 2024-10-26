
from dataclasses import dataclass
from typing import Optional
import os
from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime
@dataclass
class Config:
    """Configuration for the chatbot application."""
    REGION: str = os.getenv('AWS_REGION', 'us-east-1')
    MAX_HISTORY: int = 50
    CONTEXT_WINDOW: int = 5
    URL_EXPIRY: int = 3600

@dataclass
class Message:
    """Represents a single message in the conversation."""
    role: str
    content: str
    timestamp: datetime
    citations: Optional[List[Dict]] = None
    metadata: Optional[Dict] = None

class ConversationManager:
    """Manages conversation state and history."""
    def __init__(self):
        self.initialize_session()
    
    def initialize_session(self):
        """Initialize or recover session state."""
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return ""
    
    def add_message(self, role: str, content: str, citations: Optional[List[Dict]] = None):
        """Add a new message to the conversation history."""
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now(),
            citations=citations
        )
        self.session_state.conversation_history.append(message)
        self.session_state.messages.append({
            "role": role,
            "content": content
        })
        
        # Trim history if it exceeds maximum length
        if len(self.session_state.conversation_history) > self.config.MAX_HISTORY:
            self.session_state.conversation_history = \
                self.session_state.conversation_history[-self.config.MAX_HISTORY:]
            self.session_state.messages = \
                self.session_state.messages[-self.config.MAX_HISTORY:]
    
    def get_conversation_context(self) -> List[Dict]:
        """Get recent conversation context for the model."""
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in self.session_state.conversation_history[-self.config.CONTEXT_WINDOW:]
        ]