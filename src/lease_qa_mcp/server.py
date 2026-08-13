from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

import httpx
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from pydantic import TypeAdapter, ValidationError

from lease_qa_mcp import leaseclear
from lease_qa_mcp.leaseclear import LeaseClearError
from lease_qa_mcp.schemas import LeaseQAResponse

mcp = FastMCP("lease-qa", log_level="WARNING")
_DOCUMENT_IDS: TypeAdapter[list[UUID] | None] = TypeAdapter(list[UUID] | None)


def _parse_document_ids(raw: object) -> list[UUID] | None:
    try:
        ids = _DOCUMENT_IDS.validate_python(raw)
    except ValidationError as exc:
        raise ToolError("document_ids must be a list of UUIDs") from exc
    return ids or None


@mcp.tool()
async def lease_qa(
    question: Annotated[str, "A single neutral question about lease terms."],
    ctx: Context[Any, Any, Any],
) -> LeaseQAResponse:
    """
    Ask one neutral, precise question about lease terms. Returns an answer grounded
    in the lease, or states that the lease does not address the question.
    """
    meta = ctx.request_context.meta
    raw_ids = getattr(meta, "document_ids", None) if meta else None
    document_ids = _parse_document_ids(raw_ids)

    text = question.strip()
    if not text:
        raise ToolError("question must not be empty")
    try:
        return await leaseclear.ask(text, document_ids)
    except LeaseClearError as exc:
        raise ToolError(str(exc)) from exc
    except httpx.RequestError as exc:
        raise ToolError(f"LeaseClear unreachable: {exc}") from exc


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
