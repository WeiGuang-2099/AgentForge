"""Tests for memory system (app.core.memory)."""
import pytest

from app.core.memory import ShortTermMemory, LongTermMemory, MemoryManager


# --- ShortTermMemory tests ---

def test_short_term_add_and_get():
    """ShortTermMemory add/get_context works."""
    mem = ShortTermMemory(window_size=10)
    mem.add("conv1", {"role": "user", "content": "Hello"})
    mem.add("conv1", {"role": "assistant", "content": "Hi there"})
    
    context = mem.get_context("conv1")
    assert len(context) == 2
    assert context[0]["content"] == "Hello"
    assert context[1]["content"] == "Hi there"


def test_short_term_window():
    """ShortTermMemory respects window_size (oldest messages dropped)."""
    mem = ShortTermMemory(window_size=3)
    for i in range(5):
        mem.add("conv1", {"role": "user", "content": f"msg{i}"})
    
    context = mem.get_context("conv1")
    assert len(context) == 3
    # Should keep the last 3 messages (msg2, msg3, msg4)
    assert context[0]["content"] == "msg2"
    assert context[2]["content"] == "msg4"


def test_short_term_clear():
    """ShortTermMemory clear removes messages."""
    mem = ShortTermMemory()
    mem.add("conv1", {"role": "user", "content": "Hello"})
    assert len(mem.get_context("conv1")) == 1
    
    mem.clear("conv1")
    assert len(mem.get_context("conv1")) == 0


# --- MemoryManager tests ---

def test_memory_manager_disabled():
    """MemoryManager with enabled=False returns empty context."""
    manager = MemoryManager(enabled=False)
    context = manager.get_relevant_context("conv1", "test query")
    assert context == []


def test_memory_manager_add_message():
    """MemoryManager.add_message stores in short-term."""
    manager = MemoryManager(enabled=True)
    # Don't initialize long-term (no ChromaDB)
    manager.add_message("conv1", "user", "Hello world")
    
    messages = manager.short_term.get_context("conv1")
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello world"


# --- LongTermMemory tests ---

def test_long_term_not_available():
    """LongTermMemory returns empty list when ChromaDB unavailable."""
    ltm = LongTermMemory()
    # Don't call initialize(), so _collection is None
    assert ltm.is_available is False
    result = ltm.search("test query")
    assert result == []
