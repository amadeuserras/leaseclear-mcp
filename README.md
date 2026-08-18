# leaseclear-mcp

A standalone [MCP](https://modelcontextprotocol.io) server that exposes lease Q&A as one tool: `lease_qa`. It asks hosted [LeaseClear](https://github.com/amadeuserras/leaseclear) a question about lease terms and returns a grounded answer.

This is a thin stdio process. By default it calls the public LeaseClear API. Override `LEASECLEAR_API_URL` only if you run your own instance.

## Install

Requires Python 3.12+.

```bash
uvx leaseclear-mcp
```

Or:

```bash
pip install leaseclear-mcp
leaseclear-mcp
```

That starts the MCP server on stdio.

## Configure

| Variable | Required | Meaning |
| --- | --- | --- |
| `LEASECLEAR_API_URL` | no | LeaseClear API URL. Defaults to `https://leaseclear-production.up.railway.app`. Set this for a local or private instance. |
| `LEASECLEAR_API_KEY` | no | LeaseClear API key (`POST /auth/api-key` while logged in). Query-only: asks questions as that user. Omit to use the public demo corpus. |

If the key is set, this server sends it on `/query`. If omitted, it uses `/auth/demo` (no account needed).

From a git checkout you can copy `.env.example` to `.env`. After `pip` / `uvx`, set overrides in the MCP host `env` block instead.

### Cursor / Claude Desktop example

```json
{
  "mcpServers": {
    "lease-qa": {
      "command": "uvx",
      "args": ["leaseclear-mcp"]
    }
  }
}
```

To use your own account (or a self-hosted API), add `env`:

```json
{
  "mcpServers": {
    "lease-qa": {
      "command": "uvx",
      "args": ["leaseclear-mcp"],
      "env": {
        "LEASECLEAR_API_KEY": "lc_…"
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
git clone https://github.com/amadeuserras/leaseclear-mcp.git
cd leaseclear-mcp
uv sync
cp .env.example .env
uv run leaseclear-mcp
uv run ruff check .
uv run pyright
```
