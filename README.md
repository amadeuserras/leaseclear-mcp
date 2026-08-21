# leaseclear-mcp

A [Model Context Protocol](https://modelcontextprotocol.io) server that exposes [LeaseClear](https://github.com/amadeuserras/leaseclear) lease Q&A.

<!-- mcp-name: io.github.amadeuserras/leaseclear-mcp -->

Listed in the [official MCP Registry](https://registry.modelcontextprotocol.io) as `io.github.amadeuserras/leaseclear-mcp`.

## Tools

- `lease_qa` — ask one question about lease terms; returns an answer grounded in the lease, or states that the lease is silent

## Usage

Add this to your MCP client config (e.g. `claude_desktop_config.json` or Cursor `mcp.json`):

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

The package is on [PyPI](https://pypi.org/project/leaseclear-mcp/). `uvx` fetches and runs it as a local subprocess, communicating over stdio. [uv](https://docs.astral.sh/uv/getting-started/installation/) required.

### Optional environment variables


| Variable             | Description                                            | Default                       |
| -------------------- | ------------------------------------------------------ | ----------------------------- |
| `LEASECLEAR_API_KEY` | Use the server with your own LeaseClear account        | LeaseClear demo mode          |
| `LEASECLEAR_API_URL` | Override the API endpoint (local or private instances) | LeaseClear production backend |


```json
{
  "mcpServers": {
    "lease-qa": {
      "command": "uvx",
      "args": ["leaseclear-mcp"],
      "env": {
        "LEASECLEAR_API_KEY": "lc_...",
        "LEASECLEAR_API_URL": "https://..."
      }
    }
  }
}
```



## `lease_qa` usage

**Argument**

- `question` (string, required) — one question about the lease

`_meta`

- `document_ids` (string[], optional) — UUIDs of the documents to query. Omitted means all.

**Security**: The `_meta` field is used to pass metadata to the tool call that the model doesn't see. Having `document_ids` there is intentional: it prevents cross-document prompt injection because the model is never able to choose which documents it has access to. See a real-world example in [LeaseOps: prompt injection and the tenants table](https://github.com/amadeuserras/leaseops#security-prompt-injection-and-the-tenants-table).

## MCP Python SDK example

Tool call:

```python
result = await session.call_tool(
    name="lease_qa",
    arguments={
        "question": "How much is the security deposit for Yuna Kim?"
    },
    meta={
        "document_ids": [
            "a1b2c3d4-e5f..."
        ]
    }
)
```

Output:

```json
{
  "answer": "The security deposit is $6,400.00. This deposit is held in Owner's Broker's trust account [california-johnson-kim §4]."
}
```



## Tech stack

- Python 3.12
- Model Context Protocol Python SDK (`mcp[cli]`) over stdio
- `httpx` for LeaseClear API calls
- Pydantic and `pydantic-settings` for schemas and config
- `uv` and `uv_build` for running and packaging
- pytest, Ruff, and Pyright for tests, linting, and type checking


## Project structure

```
leaseclear-mcp/
├── src/leaseclear_mcp/
│   ├── server.py        # MCP server + lease_qa
│   ├── leaseclear.py    # LeaseClear HTTP client
│   ├── schemas.py
│   └── config.py
├── tests/
├── pyproject.toml
├── .env.example
└── README.md
```



## Local Development

```bash
git clone https://github.com/you/leaseclear-mcp.git
cd leaseclear-mcp
uv sync
cp .env.example .env
uv run pytest
uv run ruff check .
uv run pyright
```



### Debugging

Use the [MCP Inspector](https://github.com/modelcontextprotocol/inspector) to test the server interactively:

```bash
npx @modelcontextprotocol/inspector uvx leaseclear-mcp
```

From a checkout, use `uv run leaseclear-mcp` instead of `uvx leaseclear-mcp`.

## License

MIT