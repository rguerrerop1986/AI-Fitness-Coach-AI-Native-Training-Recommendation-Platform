# Fitness Coach MCP Server

MCP (Model Context Protocol) server that exposes Fitness Coach internal API as **tools** for AI agents and coach assistants. Communication is over **stdio** (MVP). The server does **not** access the database directly; it calls the Django Internal API via HTTP.

## Requirements

- Python 3.10+
- Django backend running with Internal API enabled (`INTERNAL_API_TOKEN` set)
- `mcp` and `httpx` (see `requirements.txt`)

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `INTERNAL_API_TOKEN` | Yes | Must match `INTERNAL_API_TOKEN` in Django settings. Used in `X-Internal-Token` header. |
| `FITNESS_API_BASE_URL` | No | Base URL for internal API. Default: `http://localhost:8000/api/internal` |

## Install and run locally

```bash
# From repo root
cd mcp/fitness_mcp_server
pip install -r requirements.txt

# Set token (must match backend .env INTERNAL_API_TOKEN)
export INTERNAL_API_TOKEN=your-internal-api-token-change-in-production

# Optional: if backend is not on localhost:8000
export FITNESS_API_BASE_URL=http://localhost:8000/api/internal

# Run MCP server (stdio)
python -m server
# or
python server.py
```

The server reads JSON-RPC from stdin and writes to stdout. Use an MCP client (e.g. Claude Desktop, Cursor, or MCP Inspector) and configure it to run:

```bash
python /path/to/mcp/fitness_mcp_server/server.py
```

with env `INTERNAL_API_TOKEN` set.

## Tools

| Tool | Description |
|------|-------------|
| `suggest_today_workout` | Get suggested workout for a client (today or given date). Args: `client_id`, optional `date` (YYYY-MM-DD). |
| `get_training_context` | Get recent training logs and context (adherence, pain trend). Args: `client_id`, optional `days` (default 14). |
| `record_training_feedback` | Record feedback for a date. Args: `client_id`, `date`, `execution_status`, optional `rpe`, `energy_level`, `pain_level`, `notes`, `executed_exercise_id`. |
| `coach_dashboard_summary` | AI Coach dashboard summary (high pain, not_done streaks, adherence). Args: `coach_id`, optional `days` (default 7). |
| `list_exercises` | List catalog exercises. Args: optional `query`, `tags` (comma-separated), `limit` (default 20). |

## Errors

- Missing or invalid `INTERNAL_API_TOKEN` → tools return `{"error": "..."}`.
- Backend unreachable or returns 4xx/5xx → error message in response.
- Invalid arguments (e.g. bad `execution_status`) → validation error in response.
