from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

import httpx
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from lease_qa_mcp import leaseclear
from lease_qa_mcp.leaseclear import LeaseClearError
from lease_qa_mcp.schemas import LeaseQAResponse

mcp = FastMCP("lease-qa", log_level="WARNING")


@mcp.tool()
async def lease_qa(
    question: Annotated[str, "A single neutral question about lease terms."],
    ctx: Context[Any, Any, Any],
) -> LeaseQAResponse:
    """
    Ask one neutral, precise question about the tenant's lease.
    The lease document is already scoped for this email. Returns an
    answer grounded in the lease, or states that the lease does not
    address the question.
    """
    meta = ctx.request_context.meta
    raw_id = getattr(meta, "document_id", None) if meta else None
    if not raw_id:
        raise ToolError("document_id missing from request metadata")
    document_id = UUID(str(raw_id))

    text = question.strip()
    if not text:
        raise ToolError("question must not be empty")
    try:
        return await leaseclear.ask(text, document_id)
    except LeaseClearError as exc:
        raise ToolError(str(exc)) from exc
    except httpx.RequestError as exc:
        raise ToolError(f"LeaseClear unreachable: {exc}") from exc


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
