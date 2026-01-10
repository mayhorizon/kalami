"""Session and agent tracking utilities."""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path

# Cache for current session/agent info (in-memory)
_current_context = {
    'session_id': None,
    'agent_id': None,
    'agent_stack': []  # Stack of agent IDs for nested agents
}


def generate_session_id():
    """Generate a unique session ID based on timestamp and process info.

    Returns:
        str: Unique session ID
    """
    timestamp = datetime.now().isoformat()
    pid = os.getpid()
    unique_str = f"{timestamp}-{pid}"
    hash_obj = hashlib.sha256(unique_str.encode())
    return hash_obj.hexdigest()[:16]


def get_current_session():
    """Get the current session ID.

    Tries multiple methods to determine session ID:
    1. Environment variable CLAUDE_SESSION_ID
    2. From .claude/session-env directory
    3. Cached value from previous call
    4. Generate new session ID

    Returns:
        str: Current session ID
    """
    # Check cached value first
    if _current_context['session_id']:
        return _current_context['session_id']

    # Check environment variable
    session_id = os.environ.get('CLAUDE_SESSION_ID')
    if session_id:
        _current_context['session_id'] = session_id
        return session_id

    # Check session-env directory
    session_env_dir = Path.home() / '.claude' / 'session-env'
    if session_env_dir.exists():
        # Look for session marker files
        session_files = list(session_env_dir.glob('session-*'))
        if session_files:
            # Use most recent session file
            latest_session = max(session_files, key=lambda p: p.stat().st_mtime)
            session_id = latest_session.stem.replace('session-', '')
            _current_context['session_id'] = session_id
            return session_id

    # Generate new session ID
    session_id = generate_session_id()
    _current_context['session_id'] = session_id
    return session_id


def get_current_agent():
    """Get the current agent ID.

    Tries multiple methods:
    1. Environment variable CLAUDE_AGENT_ID
    2. Cached value from agent stack
    3. Parse from task output directory
    4. Return None if no agent context

    Returns:
        str or None: Current agent ID or None if not in agent context
    """
    # Check environment variable
    agent_id = os.environ.get('CLAUDE_AGENT_ID')
    if agent_id:
        return agent_id

    # Check agent stack (for nested agents)
    if _current_context['agent_stack']:
        return _current_context['agent_stack'][-1]

    # Check cached value
    if _current_context['agent_id']:
        return _current_context['agent_id']

    # Try to parse from task output directory
    agent_id = parse_agent_from_environment()
    if agent_id:
        _current_context['agent_id'] = agent_id
        return agent_id

    # No agent context - return None (main Claude Code session)
    return None


def parse_agent_from_environment():
    """Parse agent ID from environment clues.

    Returns:
        str or None: Agent ID if found, None otherwise
    """
    # Check for task output directory in temp
    temp_dir = Path('/tmp/claude')
    if temp_dir.exists():
        # Look for recent task directories
        task_dirs = list(temp_dir.glob('*/tasks'))
        if task_dirs:
            # Find most recent task
            for task_dir in sorted(task_dirs, key=lambda p: p.stat().st_mtime, reverse=True):
                task_files = list(task_dir.glob('*.output'))
                if task_files:
                    # Extract agent ID from filename (e.g., a9bd232.output)
                    agent_id = task_files[0].stem
                    return agent_id

    return None


def push_agent(agent_id):
    """Push an agent onto the agent stack (for tracking nested agents).

    Args:
        agent_id: Agent ID to push
    """
    _current_context['agent_stack'].append(agent_id)
    _current_context['agent_id'] = agent_id


def pop_agent():
    """Pop an agent from the agent stack.

    Returns:
        str or None: Popped agent ID or None if stack is empty
    """
    if _current_context['agent_stack']:
        agent_id = _current_context['agent_stack'].pop()
        # Update current agent_id to parent agent or None
        _current_context['agent_id'] = (_current_context['agent_stack'][-1]
                                        if _current_context['agent_stack'] else None)
        return agent_id
    return None


def set_session(session_id):
    """Manually set the current session ID.

    Args:
        session_id: Session ID to set
    """
    _current_context['session_id'] = session_id


def set_agent(agent_id):
    """Manually set the current agent ID.

    Args:
        agent_id: Agent ID to set
    """
    _current_context['agent_id'] = agent_id


def reset_context():
    """Reset the tracking context (useful for testing)."""
    _current_context['session_id'] = None
    _current_context['agent_id'] = None
    _current_context['agent_stack'] = []


def get_user_command():
    """Attempt to extract the user command that triggered this session.

    Returns:
        str or None: User command if found
    """
    # Try to read from history.jsonl
    history_file = Path.home() / '.claude' / 'history.jsonl'
    if history_file.exists():
        try:
            with open(history_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    # Get the most recent entry
                    last_entry = json.loads(lines[-1])
                    if 'userMessage' in last_entry:
                        return last_entry['userMessage']
                    elif 'command' in last_entry:
                        return last_entry['command']
        except Exception:
            pass

    return None


def get_working_directory():
    """Get the current working directory.

    Returns:
        str: Current working directory path
    """
    return os.getcwd()


def get_session_info():
    """Get complete session information.

    Returns:
        dict: Session information including ID, working directory, etc.
    """
    return {
        'session_id': get_current_session(),
        'agent_id': get_current_agent(),
        'working_directory': get_working_directory(),
        'user_command': get_user_command(),
        'timestamp': datetime.now().isoformat()
    }
