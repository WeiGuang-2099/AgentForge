"""Memory management module - dual memory system (short-term + long-term)."""

import logging
import hashlib
from typing import Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class ShortTermMemory:
    """In-memory conversation buffer with configurable sliding window."""
    
    def __init__(self, window_size: int = 20):
        self.window_size = window_size
        self._buffers: dict[str, list[dict]] = defaultdict(list)
    
    def add(self, conversation_id: str, message: dict) -> None:
        """Add a message to the conversation buffer."""
        self._buffers[conversation_id].append(message)
        # Trim to window size
        if len(self._buffers[conversation_id]) > self.window_size:
            self._buffers[conversation_id] = self._buffers[conversation_id][-self.window_size:]
    
    def get_context(self, conversation_id: str, limit: Optional[int] = None) -> list[dict]:
        """Get recent messages from the conversation buffer."""
        messages = self._buffers.get(conversation_id, [])
        if limit:
            return messages[-limit:]
        return list(messages)
    
    def clear(self, conversation_id: str) -> None:
        """Clear the buffer for a conversation."""
        self._buffers.pop(conversation_id, None)
    
    def clear_all(self) -> None:
        """Clear all buffers."""
        self._buffers.clear()


class LongTermMemory:
    """ChromaDB-backed semantic memory for long-term retrieval."""
    
    def __init__(self, persist_directory: str = "./data/chroma",
                 collection_name: str = "agent_memory",
                 embedding_model: str = "all-MiniLM-L6-v2"):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self._client = None
        self._collection = None
    
    def initialize(self) -> None:
        """Initialize ChromaDB client and collection."""
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            
            self._client = chromadb.Client(ChromaSettings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=self.persist_directory,
                anonymized_telemetry=False
            ))
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"LongTermMemory initialized with collection '{self.collection_name}'")
        except ImportError:
            logger.warning("ChromaDB not available, long-term memory disabled")
            self._client = None
            self._collection = None
        except Exception as e:
            logger.warning(f"Failed to initialize ChromaDB: {e}")
            self._client = None
            self._collection = None
    
    @property
    def is_available(self) -> bool:
        return self._collection is not None
    
    def store(self, conversation_id: str, content: str, 
              metadata: Optional[dict] = None) -> None:
        """Store a message/summary in long-term memory."""
        if not self.is_available:
            return
        
        try:
            doc_id = hashlib.md5(
                f"{conversation_id}:{content[:100]}:{len(content)}".encode()
            ).hexdigest()
            
            meta = {"conversation_id": conversation_id}
            if metadata:
                meta.update(metadata)
            
            self._collection.upsert(
                ids=[doc_id],
                documents=[content],
                metadatas=[meta]
            )
        except Exception as e:
            logger.warning(f"Failed to store in long-term memory: {e}")
    
    def search(self, query: str, top_k: int = 5, 
               conversation_id: Optional[str] = None) -> list[dict]:
        """Search long-term memory for semantically relevant content."""
        if not self.is_available:
            return []
        
        try:
            where_filter = None
            if conversation_id:
                where_filter = {"conversation_id": conversation_id}
            
            results = self._collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where_filter
            )
            
            memories = []
            if results and results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    memory = {
                        "content": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else None
                    }
                    memories.append(memory)
            
            return memories
        except Exception as e:
            logger.warning(f"Failed to search long-term memory: {e}")
            return []
    
    def clear_collection(self) -> None:
        """Clear all data in the collection."""
        if not self.is_available:
            return
        try:
            if self._client:
                self._client.delete_collection(self.collection_name)
                self._collection = self._client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
        except Exception as e:
            logger.warning(f"Failed to clear long-term memory: {e}")


class MemoryManager:
    """Manages both short-term and long-term memory systems."""
    
    def __init__(self, short_term_window: int = 20,
                 long_term_top_k: int = 5,
                 persist_directory: str = "./data/chroma",
                 enabled: bool = True):
        self.enabled = enabled
        self.long_term_top_k = long_term_top_k
        self.short_term = ShortTermMemory(window_size=short_term_window)
        self.long_term = LongTermMemory(persist_directory=persist_directory)
    
    def initialize(self) -> None:
        """Initialize the memory system."""
        if not self.enabled:
            logger.info("Memory system is disabled")
            return
        self.long_term.initialize()
        logger.info("MemoryManager initialized")
    
    def add_message(self, conversation_id: str, role: str, content: str) -> None:
        """Add a message to short-term memory and optionally archive to long-term."""
        if not self.enabled:
            return
        
        message = {"role": role, "content": content}
        self.short_term.add(conversation_id, message)
        
        # Store assistant responses in long-term memory for future retrieval
        if role == "assistant" and content and len(content) > 50:
            self.long_term.store(
                conversation_id=conversation_id,
                content=content,
                metadata={"role": role}
            )
    
    def get_relevant_context(self, conversation_id: str, 
                              query: str) -> list[dict]:
        """Get relevant context by combining short-term window and long-term search."""
        if not self.enabled:
            return []
        
        context = []
        
        # Get long-term memories relevant to the current query
        long_term_results = self.long_term.search(
            query=query,
            top_k=self.long_term_top_k
        )
        
        if long_term_results:
            # Format as a system-style context injection
            memory_texts = []
            for mem in long_term_results:
                if mem.get("content"):
                    memory_texts.append(mem["content"])
            
            if memory_texts:
                combined = "\n---\n".join(memory_texts)
                context.append({
                    "role": "system",
                    "content": f"[Relevant memories from previous conversations]\n{combined}"
                })
        
        return context
    
    def clear_conversation(self, conversation_id: str) -> None:
        """Clear memory for a specific conversation."""
        self.short_term.clear(conversation_id)
    
    def clear_all(self) -> None:
        """Clear all memory."""
        self.short_term.clear_all()
        self.long_term.clear_collection()
