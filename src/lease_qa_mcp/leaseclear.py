from __future__ import annotations

import json
from uuid import UUID

import httpx

from lease_qa_mcp.config import settings
from lease_qa_mcp.schemas import LeaseQAResponse

_TIMEOUT = 60.0
_demo_token: str | None = None


class LeaseClearError(Exception):
    """Raised when the LeaseClear HTTP API returns an error or unexpected payload."""


class _DemoUnauthorized(LeaseClearError):
    """Raised when LeaseClear rejects a demo JWT."""


async def _read_sse_answer(response: httpx.Response) -> str | None:
    event = ""
    data_lines: list[str] = []
    async for line in response.aiter_lines():
        if line.startswith("event:"):
            event = line.removeprefix("event:").strip()
        elif line.startswith("data:"):
            data_lines.append(line.removeprefix("data:").lstrip(" "))
        elif line == "":
            if event == "done" and data_lines:
                payload = json.loads("\n".join(data_lines))
                answer = payload.get("answer")
                if not isinstance(answer, str):
                    raise LeaseClearError("LeaseClear done event missing string answer")
                return answer.strip()
            event = ""
            data_lines = []
    return None


def _api_key() -> str | None:
    return settings.leaseclear_api_key or None


def _drop_demo_token() -> None:
    global _demo_token
    _demo_token = None


async def _get_demo_token() -> str:
    global _demo_token
    if _demo_token is not None:
        return _demo_token
    async with httpx.AsyncClient(
        base_url=settings.leaseclear_base_url, timeout=_TIMEOUT
    ) as client:
        response = await client.post("/auth/demo")
    if response.status_code == 503:
        raise LeaseClearError(
            "LeaseClear demo auth unavailable — is the demo user seeded?"
        )
    if response.status_code >= 400:
        raise LeaseClearError(
            f"LeaseClear auth failed ({response.status_code}): {response.text}"
        )
    token = response.json().get("access_token")
    if not isinstance(token, str) or not token:
        raise LeaseClearError("LeaseClear auth response missing access_token")
    _demo_token = token
    return token


async def _bearer_token() -> str:
    return _api_key() or await _get_demo_token()


async def _query(question: str, document_ids: list[UUID] | None) -> str:
    using_api_key = _api_key() is not None
    headers = {
        "Authorization": f"Bearer {await _bearer_token()}",
        "Accept": "text/event-stream",
    }
    payload: dict[str, object] = {"question": question}
    if document_ids:
        payload["document_ids"] = [str(id) for id in document_ids]
    async with (
        httpx.AsyncClient(
            base_url=settings.leaseclear_base_url, timeout=_TIMEOUT
        ) as client,
        client.stream("POST", "/query", json=payload, headers=headers) as response,
    ):
        if response.status_code == 401 and using_api_key:
            raise LeaseClearError("LeaseClear rejected the API key")
        if response.status_code == 401:
            await response.aread()
            raise _DemoUnauthorized("LeaseClear rejected the demo token")
        if response.status_code >= 400:
            body = (await response.aread()).decode()
            raise LeaseClearError(
                f"LeaseClear query failed ({response.status_code}): {body}"
            )
        answer = await _read_sse_answer(response)
    if answer is None:
        raise LeaseClearError("LeaseClear query stream ended without a done event")
    return answer


async def ask(question: str, document_ids: list[UUID] | None = None) -> LeaseQAResponse:
    try:
        answer = await _query(question, document_ids)
    except _DemoUnauthorized:
        _drop_demo_token()
        answer = await _query(question, document_ids)
    return LeaseQAResponse(answer=answer)
