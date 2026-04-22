"""Usage statistics recording utility."""
import logging
from typing import Optional

from app.models.usage import UsageRecord

logger = logging.getLogger(__name__)


async def record_usage(
    db_session,
    agent_name: str,
    model: str,
    usage: dict,
    user_id: Optional[str] = None,
) -> None:
    """
    Record a single LLM usage entry.

    Silently logs errors to avoid disrupting the chat flow.
    """
    try:
        record = UsageRecord(
            user_id=user_id,
            agent_name=agent_name,
            model=model,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )
        db_session.add(record)
        await db_session.commit()
    except Exception as e:
        logger.error(f"Failed to record usage: {e}")
