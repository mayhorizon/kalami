#!/usr/bin/env python3
"""CLI tool for querying agent state logs."""

import os
import sys
import argparse
import json
from datetime import datetime

# Add parent directories to path
PARENT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(PARENT_DIR, 'lib'))
sys.path.insert(0, os.path.join(PARENT_DIR, 'db'))

from init_db import get_connection, get_db_stats
from compressor import get_data_from_row, decompress_data, format_size
from session_tracker import get_current_session


def list_sessions(args):
    """List all sessions."""
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM sessions ORDER BY started_at DESC"
    if args.limit:
        query += f" LIMIT {args.limit}"

    cursor.execute(query)
    sessions = cursor.fetchall()

    if not sessions:
        print("No sessions found.")
        return

    print(f"\n{'Session ID':<20} {'Started At':<25} {'Ended At':<25} {'Working Dir':<30}")
    print("-" * 100)

    for session in sessions:
        session_id = session['session_id']
        started = session['started_at']
        ended = session['ended_at'] or 'Running'
        working_dir = session['working_directory'] or 'N/A'

        print(f"{session_id:<20} {started:<25} {ended:<25} {working_dir:<30}")

    conn.close()


def list_agents(args):
    """List agents for a session."""
    conn = get_connection()
    cursor = conn.cursor()

    session_id = args.session if args.session != 'current' else get_current_session()

    cursor.execute('''
        SELECT * FROM agents
        WHERE session_id = ?
        ORDER BY created_at DESC
    ''', (session_id,))

    agents = cursor.fetchall()

    if not agents:
        print(f"No agents found for session {session_id}")
        return

    print(f"\nAgents for session: {session_id}\n")
    print(f"{'Agent ID':<12} {'Name':<25} {'Type':<15} {'Status':<12} {'Created At':<25}")
    print("-" * 100)

    for agent in agents:
        agent_id = agent['agent_id']
        name = agent['agent_name']
        agent_type = agent['agent_type'] or 'N/A'
        status = agent['status']
        created = agent['created_at']

        print(f"{agent_id:<12} {name:<25} {agent_type:<15} {status:<12} {created:<25}")

    conn.close()


def list_tool_calls(args):
    """List tool calls for an agent or session."""
    conn = get_connection()
    cursor = conn.cursor()

    if args.agent:
        cursor.execute('''
            SELECT * FROM tool_calls
            WHERE agent_id = ?
            ORDER BY called_at DESC
        ''', (args.agent,))
    elif args.session:
        session_id = args.session if args.session != 'current' else get_current_session()
        cursor.execute('''
            SELECT * FROM tool_calls
            WHERE session_id = ?
            ORDER BY called_at DESC
        ''', (session_id,))
    else:
        print("Error: Must specify --agent or --session")
        return

    tool_calls = cursor.fetchall()

    if not tool_calls:
        print("No tool calls found.")
        return

    print(f"\n{'ID':<8} {'Tool Name':<20} {'Agent ID':<12} {'Status':<12} {'Called At':<25}")
    print("-" * 85)

    for call in tool_calls:
        call_id = call['id']
        tool_name = call['tool_name']
        agent_id = call['agent_id'] or 'Main'
        status = call['status']
        called_at = call['called_at']

        print(f"{call_id:<8} {tool_name:<20} {agent_id:<12} {status:<12} {called_at:<25}")

    conn.close()


def view_tool_call(args):
    """View detailed information for a specific tool call."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM tool_calls WHERE id = ?', (args.call_id,))
    call = cursor.fetchone()

    if not call:
        print(f"Tool call {args.call_id} not found.")
        return

    print(f"\n=== Tool Call {args.call_id} ===\n")
    print(f"Tool Name: {call['tool_name']}")
    print(f"Agent ID: {call['agent_id'] or 'Main session'}")
    print(f"Session ID: {call['session_id']}")
    print(f"Called At: {call['called_at']}")
    print(f"Completed At: {call['completed_at'] or 'Not completed'}")
    print(f"Status: {call['status']}")
    print(f"Duration: {call['duration_ms']} ms" if call['duration_ms'] else "Duration: N/A")

    if call['error_message']:
        print(f"\nError: {call['error_message']}")

    # Extract and display parameters
    params = get_data_from_row(call, 'parameters_json', 'parameters_compressed', 'is_compressed')
    if params:
        print(f"\nParameters:")
        print(json.dumps(params, indent=2))

    # Extract and display result
    result = get_data_from_row(call, 'result_json', 'result_compressed', 'is_compressed')
    if result:
        print(f"\nResult:")
        if isinstance(result, str) and len(result) > 500:
            print(result[:500] + "... (truncated)")
        else:
            print(json.dumps(result, indent=2) if isinstance(result, dict) else result)

    conn.close()


def list_modifications(args):
    """List file modifications."""
    conn = get_connection()
    cursor = conn.cursor()

    if args.file_path:
        cursor.execute('''
            SELECT * FROM modifications
            WHERE file_path LIKE ?
            ORDER BY modified_at DESC
        ''', (f'%{args.file_path}%',))
    elif args.agent:
        cursor.execute('''
            SELECT * FROM modifications
            WHERE agent_id = ?
            ORDER BY modified_at DESC
        ''', (args.agent,))
    else:
        cursor.execute('SELECT * FROM modifications ORDER BY modified_at DESC LIMIT 50')

    mods = cursor.fetchall()

    if not mods:
        print("No modifications found.")
        return

    print(f"\n{'ID':<8} {'Type':<20} {'File Path':<40} {'Modified At':<25}")
    print("-" * 100)

    for mod in mods:
        mod_id = mod['id']
        mod_type = mod['modification_type']
        file_path = mod['file_path']
        modified_at = mod['modified_at']

        print(f"{mod_id:<8} {mod_type:<20} {file_path:<40} {modified_at:<25}")

    conn.close()


def export_session(args):
    """Export session data."""
    conn = get_connection()
    cursor = conn.cursor()

    session_id = args.session if args.session != 'current' else get_current_session()

    # Get session info
    cursor.execute('SELECT * FROM sessions WHERE session_id = ?', (session_id,))
    session = cursor.fetchone()

    if not session:
        print(f"Session {session_id} not found.")
        return

    # Get agents
    cursor.execute('SELECT * FROM agents WHERE session_id = ?', (session_id,))
    agents = cursor.fetchall()

    # Get tool calls
    cursor.execute('SELECT * FROM tool_calls WHERE session_id = ?', (session_id,))
    tool_calls = cursor.fetchall()

    # Get modifications
    cursor.execute('''
        SELECT m.* FROM modifications m
        JOIN tool_calls tc ON m.tool_call_id = tc.id
        WHERE tc.session_id = ?
    ''', (session_id,))
    modifications = cursor.fetchall()

    # Build export data
    export_data = {
        'session': dict(session),
        'agents': [dict(a) for a in agents],
        'tool_calls': [dict(tc) for tc in tool_calls],
        'modifications': [dict(m) for m in modifications]
    }

    # Output as JSON
    output = json.dumps(export_data, indent=2)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Session data exported to {args.output}")
    else:
        print(output)

    conn.close()


def show_stats(args):
    """Show database statistics."""
    stats = get_db_stats()

    print("\n=== Agent State Database Statistics ===\n")

    for key, value in stats.items():
        if key == 'database_size_bytes':
            print(f"{key}: {format_size(value)}")
        else:
            print(f"{key}: {value}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='Query agent state logs')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Sessions command
    sessions_parser = subparsers.add_parser('sessions', help='List sessions')
    sessions_parser.add_argument('--limit', type=int, help='Limit number of results')

    # Agents command
    agents_parser = subparsers.add_parser('agents', help='List agents')
    agents_parser.add_argument('--session', required=True, help='Session ID (or "current")')

    # Tools command
    tools_parser = subparsers.add_parser('tools', help='List tool calls')
    tools_parser.add_argument('--agent', help='Agent ID')
    tools_parser.add_argument('--session', help='Session ID (or "current")')

    # View tool call command
    view_parser = subparsers.add_parser('view-call', help='View tool call details')
    view_parser.add_argument('call_id', type=int, help='Tool call ID')

    # Modifications command
    mods_parser = subparsers.add_parser('mods', help='List modifications')
    mods_parser.add_argument('--file-path', help='Filter by file path')
    mods_parser.add_argument('--agent', help='Filter by agent ID')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export session data')
    export_parser.add_argument('--session', required=True, help='Session ID (or "current")')
    export_parser.add_argument('--output', help='Output file (default: stdout)')

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show database statistics')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Route to appropriate handler
    handlers = {
        'sessions': list_sessions,
        'agents': list_agents,
        'tools': list_tool_calls,
        'view-call': view_tool_call,
        'mods': list_modifications,
        'export': export_session,
        'stats': show_stats
    }

    handler = handlers.get(args.command)
    if handler:
        handler(args)
    else:
        print(f"Unknown command: {args.command}")
        parser.print_help()


if __name__ == '__main__':
    main()
