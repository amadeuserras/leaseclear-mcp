from __future__ import annotations

from collections.abc import Iterator
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from lease_qa_mcp.schemas import LeaseQAResponse
from lease_qa_mcp.server import lease_qa


def _ctx(*, document_ids: object | None = None) -> MagicMock:
    ctx = MagicMock()
    ctx.request_context.meta = SimpleNamespace(document_ids=document_ids)
    return ctx


@pytest.fixture
def ask() -> Iterator[AsyncMock]:
    with patch("lease_qa_mcp.server.leaseclear.ask", new_callable=AsyncMock) as mock:
        yield mock


async def test_forwards_question_and_returns_answer(ask: AsyncMock) -> None:
    ask.return_value = LeaseQAResponse(answer="Rent is $2,875 per month.")
    result = await lease_qa("What is the rent?", _ctx())
    ask.assert_awaited_once_with("What is the rent?", None)
    assert result == LeaseQAResponse(answer="Rent is $2,875 per month.")


@pytest.mark.parametrize("question", ["", "   ", "\n\t"])
async def test_rejects_empty_question(question: str, ask: AsyncMock) -> None:
    with pytest.raises(ToolError, match="question must not be empty"):
        await lease_qa(question, _ctx())
    ask.assert_not_called()


@pytest.mark.parametrize(
    "document_ids",
    [
        "not-a-list",
        ["not-a-uuid"],
        123,
    ],
)
async def test_rejects_invalid_document_ids(
    document_ids: object, ask: AsyncMock
) -> None:
    with pytest.raises(ToolError, match="document_ids must be a list of UUIDs"):
        await lease_qa("What is the rent?", _ctx(document_ids=document_ids))
    ask.assert_not_called()
