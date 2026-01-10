#!/usr/bin/env python3
"""PreToolUse hook for logging agent tool calls.

This script is called by Claude Code before any tool executes.
It logs the tool call start to the state management database.
"""

import os
import sys
import json

# Add lib directory to Python path
LIB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lib')
sys.path.insert(0, LIB_DIR)

try:
    from logger import log_tool_call_start, log_session_start
    from session_tracker import get_current_session, get_current_agent
except ImportError as e:
    # If imports fail, allow operation and log error
    error_msg = {"systemMessage": f"Agent logger import error: {e}"}
    print(json.dumps(error_msg), file=sys.stdout)
    sys.exit(0)


def main():
    """Main entry point for PreToolUse hook."""
    try:
        # Read input from stdin
        input_data = json.load(sys.stdin)

        # Extract tool information
        tool_name = input_data.get('tool_name', 'Unknown')
        parameters = input_data.get('parameters', {})

        # Get session and agent context
        session_id = get_current_session()
        agent_id = get_current_agent()

        # Ensure session is logged
        log_session_start(session_id)

        # Log tool call start
        call_id = log_tool_call_start(
            tool_name=tool_name,
            parameters=parameters,
            agent_id=agent_id,
            session_id=session_id
        )

        # Return call_id for PostToolUse to reference
        # (Claude Code should pass this through, but we'll also use timestamp matching)
        output = {
            "call_id": call_id,
            "timestamp": input_data.get('timestamp', None)
        }

        print(json.dumps(output), file=sys.stdout)

    except Exception as e:
        # On any error, allow the operation and log
        error_output = {
            "systemMessage": f"Agent logger error in PreToolUse: {str(e)}"
        }
        print(json.dumps(error_output), file=sys.stdout)

    finally:
        # ALWAYS exit 0 - never block operations due to logging errors
        sys.exit(0)


if __name__ == '__main__':
    main()
