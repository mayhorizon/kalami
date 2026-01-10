"""Main logging module for agent state management."""

import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path

# Import our modules
sys.path.insert(0, os.path.dirname(__file__))
from compressor import compress_if_large, compress_data
from session_tracker import get_current_session, get_current_agent, get_working_directory, get_user_command

# Import database module
parent_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(parent_dir, 'db'))
from init_db import get_connection, DB_PATH


def log_session_start(session_id=None, user_command=None, working_directory=None, metadata=None):
    """Log the start of a new session.

    Args:
        session_id: Session ID (auto-generated if None)
        user_command: User command that started the session
        working_directory: Working directory path
        metadata: Additional metadata as dict

    Returns:
        str: Session ID
    """
    if session_id is None:
        session_id = get_current_session()
    if working_directory is None:
        working_directory = get_working_directory()
    if user_command is None:
        user_command = get_user_command()

    try:
        conn = get_connection()
        cursor = conn.cursor()

        metadata_json = json.dumps(metadata) if metadata else None

        cursor.execute('''
            INSERT OR IGNORE INTO sessions (session_id, user_command, working_directory, metadata_json)
            VALUES (?, ?, ?, ?)
        ''', (session_id, user_command, working_directory, metadata_json))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging session start: {e}", file=sys.stderr)

    return session_id


def log_session_end(session_id=None):
    """Log the end of a session.

    Args:
        session_id: Session ID (uses current session if None)
    """
    if session_id is None:
        session_id = get_current_session()

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE sessions
            SET ended_at = CURRENT_TIMESTAMP
            WHERE session_id = ?
        ''', (session_id,))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging session end: {e}", file=sys.stderr)


def log_agent_start(agent_id, agent_name, agent_type=None, prompt=None,
                    user_command=None, session_id=None):
    """Log the start of an agent.

    Args:
        agent_id: Unique agent ID
        agent_name: Name of the agent
        agent_type: Type of agent ('Explore', 'Plan', 'custom', etc.)
        prompt: Prompt given to the agent
        user_command: User command that triggered the agent
        session_id: Session ID (uses current if None)

    Returns:
        str: Agent ID
    """
    if session_id is None:
        session_id = get_current_session()

    # Ensure session exists
    log_session_start(session_id)

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR IGNORE INTO agents
            (agent_id, session_id, agent_name, agent_type, prompt, user_command, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (agent_id, session_id, agent_name, agent_type, prompt, user_command, 'running'))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging agent start: {e}", file=sys.stderr)

    return agent_id


def log_agent_end(agent_id, status='completed'):
    """Log the end of an agent.

    Args:
        agent_id: Agent ID
        status: Final status ('completed', 'failed', etc.)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE agents
            SET completed_at = CURRENT_TIMESTAMP, status = ?
            WHERE agent_id = ?
        ''', (status, agent_id))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging agent end: {e}", file=sys.stderr)


def log_tool_call_start(tool_name, parameters, agent_id=None, session_id=None):
    """Log the start of a tool call.

    Args:
        tool_name: Name of the tool being called
        parameters: Tool parameters (dict)
        agent_id: Agent ID (uses current if None, can be None for main session)
        session_id: Session ID (uses current if None)

    Returns:
        int: Tool call ID
    """
    if session_id is None:
        session_id = get_current_session()
    if agent_id is None:
        agent_id = get_current_agent()

    # Ensure session exists
    log_session_start(session_id)

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Compress parameters if large
        params_data, is_compressed = compress_if_large(parameters)

        if is_compressed:
            cursor.execute('''
                INSERT INTO tool_calls
                (agent_id, session_id, tool_name, parameters_compressed, is_compressed, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (agent_id, session_id, tool_name, params_data, 1, 'started'))
        else:
            cursor.execute('''
                INSERT INTO tool_calls
                (agent_id, session_id, tool_name, parameters_json, is_compressed, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (agent_id, session_id, tool_name, params_data, 0, 'started'))

        call_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return call_id
    except Exception as e:
        print(f"Error logging tool call start: {e}", file=sys.stderr)
        return None


def log_tool_call_end(call_id, result, duration_ms=None, status='completed', error_message=None):
    """Log the completion of a tool call.

    Args:
        call_id: Tool call ID from log_tool_call_start
        result: Tool result (dict or str)
        duration_ms: Duration in milliseconds
        status: Status ('completed', 'failed', etc.)
        error_message: Error message if failed
    """
    if call_id is None:
        return

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Compress result if large
        result_data, result_compressed = compress_if_large(result)

        if result_compressed:
            cursor.execute('''
                UPDATE tool_calls
                SET completed_at = CURRENT_TIMESTAMP,
                    result_compressed = ?,
                    duration_ms = ?,
                    status = ?,
                    error_message = ?
                WHERE id = ?
            ''', (result_data, duration_ms, status, error_message, call_id))
        else:
            cursor.execute('''
                UPDATE tool_calls
                SET completed_at = CURRENT_TIMESTAMP,
                    result_json = ?,
                    duration_ms = ?,
                    status = ?,
                    error_message = ?
                WHERE id = ?
            ''', (result_data, duration_ms, status, error_message, call_id))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging tool call end: {e}", file=sys.stderr)


def log_modification(tool_call_id, modification_type, file_path,
                     old_content=None, new_content=None, agent_id=None):
    """Log a file modification.

    Args:
        tool_call_id: Tool call ID that caused the modification
        modification_type: Type of modification ('file_write', 'file_edit', etc.)
        file_path: Path to the modified file
        old_content: Old content (for edits)
        new_content: New content
        agent_id: Agent ID (uses current if None)
    """
    if agent_id is None:
        agent_id = get_current_agent()

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Compute content hashes
        old_hash = hashlib.sha256(old_content.encode()).hexdigest() if old_content else None
        new_hash = hashlib.sha256(new_content.encode()).hexdigest() if new_content else None

        # Compute and compress diff if both contents exist
        diff_compressed = None
        if old_content and new_content:
            # Simple diff: store both as JSON
            diff_data = {
                'old': old_content,
                'new': new_content
            }
            diff_compressed = compress_data(diff_data)

        cursor.execute('''
            INSERT INTO modifications
            (tool_call_id, agent_id, modification_type, file_path,
             old_content_hash, new_content_hash, diff_compressed)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (tool_call_id, agent_id, modification_type, file_path,
              old_hash, new_hash, diff_compressed))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging modification: {e}", file=sys.stderr)


def create_snapshot(snapshot_type, state_data, agent_id=None, session_id=None):
    """Create a state snapshot.

    Args:
        snapshot_type: Type of snapshot ('agent_start', 'agent_end', etc.)
        state_data: State data as dict
        agent_id: Agent ID (uses current if None)
        session_id: Session ID (uses current if None)

    Returns:
        int: Snapshot ID
    """
    if session_id is None:
        session_id = get_current_session()
    if agent_id is None:
        agent_id = get_current_agent()

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Compress state if large
        state, is_compressed = compress_if_large(state_data)

        if is_compressed:
            cursor.execute('''
                INSERT INTO state_snapshots
                (session_id, agent_id, snapshot_type, state_compressed, is_compressed)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, agent_id, snapshot_type, state, 1))
        else:
            cursor.execute('''
                INSERT INTO state_snapshots
                (session_id, agent_id, snapshot_type, state_json, is_compressed)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, agent_id, snapshot_type, state, 0))

        snapshot_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return snapshot_id
    except Exception as e:
        print(f"Error creating snapshot: {e}", file=sys.stderr)
        return None
