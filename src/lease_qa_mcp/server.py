from __future__ import annotations

from uuid import UUID

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from lease_qa_mcp import leaseclear
from lease_qa_mcp.leaseclear import LeaseClearError
from lease_qa_mcp.schemas import LeaseQAResponse

mcp = FastMCP("lease-qa", log_level="WARNING")


@mcp.tool()
async def lease_qa(question: str, document_id: UUID) -> LeaseQAResponse:
    """Ask LeaseClear a lease question scoped to one document."""
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
