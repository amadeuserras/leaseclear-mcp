# lease-qa-mcp

A standalone [MCP](https://modelcontextprotocol.io) server that exposes lease Q&A as one tool: `lease_qa`. It asks [LeaseClear](https://github.com/amadeuserras/leaseclear) a question about a specific lease document and returns a grounded answer.

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

LeaseClear must be up and demo-auth seeded — this server uses `/auth/demo`, then streams `/query`.

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
| **Metadata** | `document_id` (UUID) — which lease to query; **not** an LLM-visible argument |
| **Returns** | `{ "answer": "..." }` — LeaseClear’s grounded answer (or that the lease is silent) |

`document_id` is passed in request metadata on purpose. The model only chooses the question; the host chooses which document is in scope. That keeps untrusted text from picking another tenant’s lease.

### Errors

Failures surface as MCP tool errors, including:

- missing / invalid `document_id` in metadata
- empty question
- LeaseClear auth or query failures
- LeaseClear unreachable

## Development

```bash
uv run ruff check .
uv run pyright
```
