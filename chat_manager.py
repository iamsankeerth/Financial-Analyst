"""
Chat Manager with Redis Storage
Supports multiple chats per user with persistent conversation history
"""
import json
import uuid
from datetime import datetime
from typing import Optional
import redis

# Redis connection settings
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

# Try to connect to Redis, fallback to in-memory if not available
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    redis_client.ping()  # Test connection
    REDIS_AVAILABLE = True
    print("✅ Redis connected successfully")
except:
    redis_client = None
    REDIS_AVAILABLE = False
    print("⚠️ Redis not available, using in-memory storage")

# In-memory fallback storage
memory_storage = {}


class ChatManager:
    """Manages multiple chats per user with Redis persistence"""
    
    def __init__(self, user_id: str = "default_user"):
        self.user_id = user_id
        self.max_history = 20  # Max messages per chat
    
    def _get_key(self, chat_id: str) -> str:
        """Generate Redis key for a chat"""
        return f"chat:{self.user_id}:{chat_id}"
    
    def _get_chats_key(self) -> str:
        """Key for user's chat list"""
        return f"chats:{self.user_id}"
    
    def create_chat(self, title: Optional[str] = None) -> str:
        """Create a new chat and return its ID"""
        chat_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().isoformat()
        
        chat_meta = {
            "id": chat_id,
            "title": title or f"Chat {chat_id}",
            "created_at": timestamp,
            "updated_at": timestamp,
            "message_count": 0
        }
        
        if REDIS_AVAILABLE:
            # Store chat metadata
            redis_client.hset(self._get_chats_key(), chat_id, json.dumps(chat_meta))
            # Initialize empty history
            redis_client.set(self._get_key(chat_id), json.dumps([]))
        else:
            # In-memory fallback
            if self.user_id not in memory_storage:
                memory_storage[self.user_id] = {"chats": {}, "histories": {}}
            memory_storage[self.user_id]["chats"][chat_id] = chat_meta
            memory_storage[self.user_id]["histories"][chat_id] = []
        
        return chat_id
    
    def get_all_chats(self) -> list:
        """Get all chats for the user"""
        if REDIS_AVAILABLE:
            chats_data = redis_client.hgetall(self._get_chats_key())
            chats = [json.loads(v) for v in chats_data.values()]
        else:
            if self.user_id in memory_storage:
                chats = list(memory_storage[self.user_id]["chats"].values())
            else:
                chats = []
        
        # Sort by updated_at descending
        return sorted(chats, key=lambda x: x.get("updated_at", ""), reverse=True)
    
    def get_history(self, chat_id: str) -> list:
        """Get conversation history for a chat"""
        if REDIS_AVAILABLE:
            data = redis_client.get(self._get_key(chat_id))
            return json.loads(data) if data else []
        else:
            if self.user_id in memory_storage:
                return memory_storage[self.user_id]["histories"].get(chat_id, [])
            return []
    
    def add_message(self, chat_id: str, query: str, response: str):
        """Add a message to chat history"""
        history = self.get_history(chat_id)
        
        message = {
            "query": query,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
        
        history.append(message)
        
        # Trim to max history
        if len(history) > self.max_history:
            history = history[-self.max_history:]
        
        if REDIS_AVAILABLE:
            redis_client.set(self._get_key(chat_id), json.dumps(history))
            # Update chat metadata
            chats_data = redis_client.hget(self._get_chats_key(), chat_id)
            if chats_data:
                chat_meta = json.loads(chats_data)
                chat_meta["updated_at"] = datetime.now().isoformat()
                chat_meta["message_count"] = len(history)
                # Update title from first query if still default
                if chat_meta["title"].startswith("Chat ") and history:
                    chat_meta["title"] = history[0]["query"][:30] + "..."
                redis_client.hset(self._get_chats_key(), chat_id, json.dumps(chat_meta))
        else:
            if self.user_id in memory_storage:
                memory_storage[self.user_id]["histories"][chat_id] = history
                if chat_id in memory_storage[self.user_id]["chats"]:
                    memory_storage[self.user_id]["chats"][chat_id]["updated_at"] = datetime.now().isoformat()
                    memory_storage[self.user_id]["chats"][chat_id]["message_count"] = len(history)
    
    def delete_chat(self, chat_id: str):
        """Delete a chat"""
        if REDIS_AVAILABLE:
            redis_client.delete(self._get_key(chat_id))
            redis_client.hdel(self._get_chats_key(), chat_id)
        else:
            if self.user_id in memory_storage:
                memory_storage[self.user_id]["chats"].pop(chat_id, None)
                memory_storage[self.user_id]["histories"].pop(chat_id, None)
    
    def clear_chat(self, chat_id: str):
        """Clear history of a chat but keep the chat"""
        if REDIS_AVAILABLE:
            redis_client.set(self._get_key(chat_id), json.dumps([]))
        else:
            if self.user_id in memory_storage:
                memory_storage[self.user_id]["histories"][chat_id] = []
    
    def rename_chat(self, chat_id: str, new_title: str):
        """Rename a chat"""
        if REDIS_AVAILABLE:
            chats_data = redis_client.hget(self._get_chats_key(), chat_id)
            if chats_data:
                chat_meta = json.loads(chats_data)
                chat_meta["title"] = new_title
                redis_client.hset(self._get_chats_key(), chat_id, json.dumps(chat_meta))
        else:
            if self.user_id in memory_storage:
                if chat_id in memory_storage[self.user_id]["chats"]:
                    memory_storage[self.user_id]["chats"][chat_id]["title"] = new_title


# Convenience functions for the existing code
_default_manager = ChatManager()
_current_chat_id = None


def get_or_create_chat() -> str:
    """Get current chat or create a new one"""
    global _current_chat_id
    chats = _default_manager.get_all_chats()
    
    if not chats:
        _current_chat_id = _default_manager.create_chat()
    elif _current_chat_id is None:
        _current_chat_id = chats[0]["id"]
    
    return _current_chat_id


def set_current_chat(chat_id: str):
    """Set the current active chat"""
    global _current_chat_id
    _current_chat_id = chat_id


def get_current_history() -> list:
    """Get history for current chat"""
    chat_id = get_or_create_chat()
    return _default_manager.get_history(chat_id)


def add_to_current_history(query: str, response: str):
    """Add message to current chat"""
    chat_id = get_or_create_chat()
    _default_manager.add_message(chat_id, query, response)


def get_manager() -> ChatManager:
    """Get the chat manager instance"""
    return _default_manager


if __name__ == "__main__":
    # Test the chat manager
    print("Testing Chat Manager...")
    
    manager = ChatManager("test_user")
    
    # Create a chat
    chat_id = manager.create_chat("Tesla Analysis")
    print(f"Created chat: {chat_id}")
    
    # Add messages
    manager.add_message(chat_id, "Show Tesla stock", "import yfinance...")
    manager.add_message(chat_id, "Add moving average", "import yfinance...MA...")
    
    # Get history
    history = manager.get_history(chat_id)
    print(f"History: {len(history)} messages")
    
    # Get all chats
    chats = manager.get_all_chats()
    print(f"Total chats: {len(chats)}")
    
    print("✅ Chat Manager test passed!")
