# lease-qa-mcp

A standalone [MCP](https://modelcontextprotocol.io) server that exposes lease Q&A as one tool: `lease_qa`. It asks [LeaseClear](https://github.com/amadeuserras/leaseclear) a question about lease terms and returns a grounded answer.

## Runs where your data lives

This server is a thin stdio process. Point `LEASECLEAR_BASE_URL` at a LeaseClear instance on your machine or private network — documents stay in that environment. Nothing here hosts or uploads leases.

## Install

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/amadeuserras/lease-qa-mcp.git
cd lease-qa-mcp
uv sync
```

## Configure

```bash
cp .env.example .env
```

| Variable | Required | Meaning |
| --- | --- | --- |
| `LEASECLEAR_BASE_URL` | yes | Base URL of a running LeaseClear API (e.g. `http://localhost:8001`) |
| `LEASECLEAR_API_KEY` | no | LeaseClear API key (`POST /auth/api-key` while logged in). Query-only: asks questions as that user. Omit to use the public demo corpus. |

If the key is set, this server sends it on `/query`. If omitted, it uses `/auth/demo` (no account needed).

## Run

```bash
uv run lease-qa-mcp
```

That starts the MCP server on stdio (how Cursor, Claude Desktop, and other MCP hosts talk to it).

### Cursor / Claude Desktop example

```json
{
  "mcpServers": {
    "lease-qa": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/lease-qa-mcp", "lease-qa-mcp"],
      "env": {
        "LEASECLEAR_BASE_URL": "http://localhost:8001"
      }
    }
  }
}
```

## Tool: `lease_qa`

| | |
| --- | --- |
| **Arguments** | `question` (string) — one neutral question about lease terms |
| **Metadata** | `document_ids` (list of UUIDs, optional) — which leases to query; **not** an LLM-visible argument |
| **Returns** | `{ "answer": "..." }` — LeaseClear’s grounded answer (or that the lease is silent) |

If the host passes `document_ids`, the question is scoped to those leases. If omitted, LeaseClear searches all leases on the authenticated account. The model only chooses the question; the host chooses whether to scope.

### Errors

Failures surface as MCP tool errors, including:

- invalid `document_ids` in metadata
- empty question
- LeaseClear auth or query failures
- LeaseClear unreachable

## Development

```bash
uv run ruff check .
uv run pyright
```
