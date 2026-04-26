"""Tests for agent engine (app.core.agent)."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.agent import AgentProfile, AgentRegistry, AgentEngine, AgentNotFoundError


# --- AgentRegistry tests ---

def test_agent_registry_register():
    """register adds agent and list_all returns it."""
    registry = AgentRegistry()
    profile = AgentProfile(
        name="test", display_name="Test", description="desc",
        model="gpt-4", system_prompt="hello"
    )
    registry.register(profile)
    agents = registry.list_all()
    assert len(agents) == 1
    assert agents[0].name == "test"


def test_agent_registry_get():
    """get returns correct agent by name."""
    registry = AgentRegistry()
    profile = AgentProfile(
        name="agent1", display_name="Agent 1", description="desc",
        model="gpt-4", system_prompt="prompt"
    )
    registry.register(profile)
    result = registry.get("agent1")
    assert result is not None
    assert result.name == "agent1"
    assert result.display_name == "Agent 1"


def test_agent_registry_unregister():
    """unregister removes agent."""
    registry = AgentRegistry()
    profile = AgentProfile(
        name="removeme", display_name="Remove", description="desc",
        model="gpt-4", system_prompt="prompt"
    )
    registry.register(profile)
    assert registry.get("removeme") is not None
    registry.unregister("removeme")
    assert registry.get("removeme") is None
    assert len(registry.list_all()) == 0


def test_agent_registry_get_not_found():
    """get returns None for nonexistent name."""
    registry = AgentRegistry()
    assert registry.get("nonexistent") is None


# --- AgentEngine tests ---

def test_engine_build_messages(sample_agent_config):
    """_build_messages constructs correct message list with system prompt."""
    engine = AgentEngine()
    profile = AgentProfile(**sample_agent_config)
    
    conversation_messages = [{"role": "user", "content": "Hello"}]
    messages = engine._build_messages(profile, conversation_messages)
    
    # First message should be system prompt
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "You are a test assistant."
    # Second message should be the user message
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "Hello"


async def test_engine_run_basic(mock_llm_client, sample_agent_config):
    """AgentEngine.run() with mocked LLM returns a response."""
    engine = AgentEngine()
    profile = AgentProfile(**sample_agent_config)
    engine.registry.register(profile)
    
    # Patch _get_llm_client to return our mock
    with patch.object(engine, '_get_llm_client', return_value=mock_llm_client):
        response = await engine.run(
            "test_agent",
            [{"role": "user", "content": "Hi there"}]
        )
    
    assert response is not None
    assert response.content == "Test response from LLM"
    assert response.model == "test-model"
