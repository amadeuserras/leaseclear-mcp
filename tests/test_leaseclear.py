from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from unittest.mock import patch
from uuid import UUID

import httpx
import pytest

from leaseclear_mcp import leaseclear
from leaseclear_mcp.config import settings
from leaseclear_mcp.leaseclear import LeaseClearError, ask

_ANSWER = "Rent is $2,875 per month."
_DOC_ID = UUID("11111111-1111-1111-1111-111111111111")
_DEMO_TOKEN = "demo-jwt"


def _sse(answer: str) -> bytes:
    done = json.dumps({"answer": answer})
    return f"event: token\ndata: {answer}\n\nevent: done\ndata: {done}\n\n".encode()


@contextmanager
def _patched_client(
    handler: Callable[[httpx.Request], httpx.Response],
) -> Iterator[None]:
    transport = httpx.MockTransport(handler)
    real_async_client = httpx.AsyncClient

    def factory(*args: object, **kwargs: object) -> httpx.AsyncClient:
        kwargs["transport"] = transport
        return real_async_client(*args, **kwargs)

    with patch("leaseclear_mcp.leaseclear.httpx.AsyncClient", side_effect=factory):
        yield


@pytest.fixture(autouse=True)
def reset_demo_token() -> None:
    leaseclear._demo_token = None


@pytest.fixture
def captured() -> list[httpx.Request]:
    return []


@pytest.fixture
def mock_client(captured: list[httpx.Request]) -> Iterator[None]:
    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        if request.url.path == "/auth/demo":
            return httpx.Response(500, text="demo must not be called")
        if request.url.path != "/query":
            return httpx.Response(404)
        expected = f"Bearer {settings.leaseclear_api_key}"
        if request.headers.get("authorization") != expected:
            return httpx.Response(401, json={"detail": "Invalid API key"})
        return httpx.Response(200, content=_sse(_ANSWER))

    with _patched_client(handler):
        yield


async def test_ask_sends_api_key_and_skips_demo(
    mock_client: None, captured: list[httpx.Request]
) -> None:
    result = await ask("What is the rent?", [_DOC_ID])
    assert result.answer == _ANSWER
    assert len(captured) == 1
    request = captured[0]
    assert request.url.path == "/query"
    assert request.headers["authorization"] == f"Bearer {settings.leaseclear_api_key}"
    body = json.loads(request.content)
    assert body == {
        "question": "What is the rent?",
        "document_ids": [str(_DOC_ID)],
    }


async def test_ask_uses_demo_when_api_key_omitted(
    monkeypatch: pytest.MonkeyPatch, captured: list[httpx.Request]
) -> None:
    monkeypatch.setattr(settings, "leaseclear_api_key", None)

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        if request.url.path == "/auth/demo":
            return httpx.Response(200, json={"access_token": _DEMO_TOKEN})
        if request.url.path != "/query":
            return httpx.Response(404)
        if request.headers.get("authorization") != f"Bearer {_DEMO_TOKEN}":
            return httpx.Response(401, json={"detail": "Invalid or expired token"})
        return httpx.Response(200, content=_sse(_ANSWER))

    with _patched_client(handler):
        result = await ask("What is the rent?")

    assert result.answer == _ANSWER
    assert [r.url.path for r in captured] == ["/auth/demo", "/query"]


async def test_ask_maps_401_to_api_key_error() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"detail": "Invalid API key"})

    with (
        _patched_client(handler),
        pytest.raises(LeaseClearError, match="rejected the API key"),
    ):
        await ask("What is the rent?")


async def test_ask_refreshes_expired_demo_token(
    monkeypatch: pytest.MonkeyPatch, captured: list[httpx.Request]
) -> None:
    monkeypatch.setattr(settings, "leaseclear_api_key", None)
    leaseclear._demo_token = "expired-jwt"
    fresh = "fresh-jwt"

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        if request.url.path == "/auth/demo":
            return httpx.Response(200, json={"access_token": fresh})
        if request.url.path != "/query":
            return httpx.Response(404)
        if request.headers.get("authorization") == "Bearer expired-jwt":
            return httpx.Response(401, json={"detail": "Invalid or expired token"})
        if request.headers.get("authorization") == f"Bearer {fresh}":
            return httpx.Response(200, content=_sse(_ANSWER))
        return httpx.Response(401, json={"detail": "Invalid or expired token"})

    with _patched_client(handler):
        result = await ask("What is the rent?")

    assert result.answer == _ANSWER
    assert [r.url.path for r in captured] == ["/query", "/auth/demo", "/query"]
    assert captured[0].headers["authorization"] == "Bearer expired-jwt"
    assert captured[2].headers["authorization"] == f"Bearer {fresh}"


async def test_ask_does_not_retry_demo_forever(
    monkeypatch: pytest.MonkeyPatch, captured: list[httpx.Request]
) -> None:
    monkeypatch.setattr(settings, "leaseclear_api_key", None)

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        if request.url.path == "/auth/demo":
            return httpx.Response(200, json={"access_token": _DEMO_TOKEN})
        return httpx.Response(401, json={"detail": "Invalid or expired token"})

    with (
        _patched_client(handler),
        pytest.raises(LeaseClearError, match="rejected the demo token"),
    ):
        await ask("What is the rent?")

    assert [r.url.path for r in captured] == [
        "/auth/demo",
        "/query",
        "/auth/demo",
        "/query",
    ]
