"""
Fitness Coach MCP Server (stdio transport).
Exposes tools that call the Django Internal API. No direct DB access.
"""
import os
import json
from datetime import date

# MCP SDK: use high-level server if available
try:
    from mcp.server.mcpserver import MCPServer
    MCP_SERVER = MCPServer("Fitness Coach")
except ImportError:
    try:
        from mcp.server.fastmcp import FastMCP
        MCP_SERVER = FastMCP("Fitness Coach")
    except ImportError:
        MCP_SERVER = None

from .client import (
    suggest_today as api_suggest_today,
    get_training_context as api_get_context,
    record_feedback as api_record_feedback,
    coach_summary as api_coach_summary,
    list_exercises as api_list_exercises,
)


def _today_str():
    return date.today().isoformat()


# --- Tool implementations (validate inputs, call API, handle errors) ---

def _suggest_today_workout(client_id: int, date_str: str | None = None) -> str:
    """Get the suggested workout for a client for today (or a given date)."""
    if not isinstance(client_id, int) or client_id <= 0:
        return json.dumps({'error': 'client_id must be a positive integer'})
    try:
        out = api_suggest_today(client_id, date_str)
        return json.dumps(out, default=str)
    except Exception as e:
        return json.dumps({'error': str(e)})


def _get_training_context(client_id: int, days: int = 14) -> str:
    """Get recent training logs and context (adherence, pain trend) for a client."""
    if not isinstance(client_id, int) or client_id <= 0:
        return json.dumps({'error': 'client_id must be a positive integer'})
    if not isinstance(days, int) or days < 1 or days > 90:
        days = 14
    try:
        out = api_get_context(client_id, days)
        return json.dumps(out, default=str)
    except Exception as e:
        return json.dumps({'error': str(e)})


def _record_training_feedback(
    client_id: int,
    date_str: str,
    execution_status: str,
    rpe: int | None = None,
    energy_level: int | None = None,
    pain_level: int | None = None,
    notes: str | None = None,
    executed_exercise_id: int | None = None,
) -> str:
    """Record training feedback for a client on a given date. execution_status: done, not_done, skipped, partial, replaced, injury_stop, sick."""
    if not isinstance(client_id, int) or client_id <= 0:
        return json.dumps({'error': 'client_id must be a positive integer'})
    valid = {'done', 'not_done', 'skipped', 'partial', 'replaced', 'injury_stop', 'sick'}
    if execution_status not in valid:
        return json.dumps({'error': f'execution_status must be one of {sorted(valid)}'})
    try:
        out = api_record_feedback(
            client_id, date_str, execution_status,
            rpe=rpe, energy_level=energy_level, pain_level=pain_level,
            notes=notes, executed_exercise_id=executed_exercise_id,
        )
        return json.dumps(out, default=str)
    except Exception as e:
        return json.dumps({'error': str(e)})


def _coach_dashboard_summary(coach_id: int, days: int = 7) -> str:
    """Get AI Coach dashboard summary: high pain clients, not_done streaks, adherence trend."""
    if not isinstance(coach_id, int) or coach_id <= 0:
        return json.dumps({'error': 'coach_id must be a positive integer'})
    if not isinstance(days, int) or days < 1 or days > 90:
        days = 7
    try:
        out = api_coach_summary(coach_id, days)
        return json.dumps(out, default=str)
    except Exception as e:
        return json.dumps({'error': str(e)})


def _list_exercises_tool(query: str | None = None, tags: str | None = None, limit: int = 20) -> str:
    """List exercises from catalog. Optional: query (search), tags (comma-separated), limit."""
    if not isinstance(limit, int) or limit < 1 or limit > 100:
        limit = 20
    try:
        out = api_list_exercises(query=query, tags=tags, limit=limit)
        return json.dumps(out, default=str)
    except Exception as e:
        return json.dumps({'error': str(e)})


# --- Register tools with MCP server ---

if MCP_SERVER is not None:
    # Register tools (names: suggest_today_workout, get_training_context, record_training_feedback, coach_dashboard_summary, list_exercises)
    if hasattr(MCP_SERVER, 'tool'):

        @MCP_SERVER.tool()
        def suggest_today_workout(client_id: int, date: str | None = None) -> str:
            """Get the suggested workout for a client for today or a given date (YYYY-MM-DD)."""
            return _suggest_today_workout(client_id, date)

        @MCP_SERVER.tool()
        def get_training_context(client_id: int, days: int = 14) -> str:
            """Get recent training logs and context (adherence, pain trend) for a client."""
            return _get_training_context(client_id, days)

        @MCP_SERVER.tool()
        def record_training_feedback(
            client_id: int,
            date: str,
            execution_status: str,
            rpe: int | None = None,
            energy_level: int | None = None,
            pain_level: int | None = None,
            notes: str | None = None,
            executed_exercise_id: int | None = None,
        ) -> str:
            """Record training feedback. execution_status: done, not_done, skipped, partial, replaced, injury_stop, sick."""
            return _record_training_feedback(
                client_id, date, execution_status,
                rpe=rpe, energy_level=energy_level, pain_level=pain_level,
                notes=notes, executed_exercise_id=executed_exercise_id,
            )

        @MCP_SERVER.tool()
        def coach_dashboard_summary(coach_id: int, days: int = 7) -> str:
            """Get AI Coach dashboard summary: high pain clients, not_done streaks, adherence trend."""
            return _coach_dashboard_summary(coach_id, days)

        @MCP_SERVER.tool()
        def list_exercises(query: str | None = None, tags: str | None = None, limit: int = 20) -> str:
            """List exercises from catalog. query: search name; tags: comma-separated (e.g. mobility, low_impact)."""
            return _list_exercises_tool(query, tags, limit)


def run_server():
    """Run MCP server with stdio transport."""
    if MCP_SERVER is None:
        raise RuntimeError('MCP SDK not installed. pip install mcp')
    # Default run() often uses stdio when no transport specified
    if hasattr(MCP_SERVER, 'run'):
        # MCPServer v2: mcp.run(transport="streamable-http" | stdio default?)
        import inspect
        sig = inspect.signature(MCP_SERVER.run)
        if 'transport' in sig.parameters:
            MCP_SERVER.run(transport='stdio')
        else:
            MCP_SERVER.run()
    else:
        raise RuntimeError('MCP server has no run() method')


if __name__ == '__main__':
    run_server()
