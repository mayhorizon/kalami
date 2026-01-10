#!/usr/bin/env python3
"""PostToolUse hook for logging agent tool call results.

This script is called by Claude Code after a tool executes.
It logs the tool call result and tracks file modifications.
"""

import os
import sys
import json
import time

# Add lib directory to Python path
LIB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lib')
sys.path.insert(0, LIB_DIR)

try:
    from logger import log_tool_call_end, log_modification
    from session_tracker import get_current_agent
except ImportError as e:
    error_msg = {"systemMessage": f"Agent logger import error: {e}"}
    print(json.dumps(error_msg), file=sys.stdout)
    sys.exit(0)


def track_file_modification(input_data, call_id):
    """Track file modifications for Write/Edit tools.

    Args:
        input_data: Input data containing tool information
        call_id: Tool call ID
    """
    try:
        tool_name = input_data.get('tool_name', '')
        parameters = input_data.get('parameters', {})
        result = input_data.get('result', {})

        agent_id = get_current_agent()

        # Determine modification type and extract content
        if tool_name == 'Write':
            file_path = parameters.get('file_path')
            new_content = parameters.get('content', '')
            if file_path:
                log_modification(
                    tool_call_id=call_id,
                    modification_type='file_write',
                    file_path=file_path,
                    old_content=None,
                    new_content=new_content,
                    agent_id=agent_id
                )

        elif tool_name == 'Edit':
            file_path = parameters.get('file_path')
            old_string = parameters.get('old_string', '')
            new_string = parameters.get('new_string', '')
            if file_path:
                log_modification(
                    tool_call_id=call_id,
                    modification_type='file_edit',
                    file_path=file_path,
                    old_content=old_string,
                    new_content=new_string,
                    agent_id=agent_id
                )

        elif tool_name == 'MultiEdit':
            file_path = parameters.get('file_path')
            edits = parameters.get('edits', [])
            if file_path:
                # Log multi-edit as a single modification
                log_modification(
                    tool_call_id=call_id,
                    modification_type='file_multi_edit',
                    file_path=file_path,
                    old_content=json.dumps(edits),
                    new_content='[multiple edits]',
                    agent_id=agent_id
                )

    except Exception as e:
        print(f"Error tracking modification: {e}", file=sys.stderr)


def main():
    """Main entry point for PostToolUse hook."""
    try:
        # Read input from stdin
        input_data = json.load(sys.stdin)

        # Extract tool information
        tool_name = input_data.get('tool_name', 'Unknown')
        result = input_data.get('result', {})
        error = input_data.get('error')

        # Get call_id from PreToolUse (if available)
        call_id = input_data.get('call_id')

        # Calculate duration if timestamps available
        start_time = input_data.get('start_timestamp')
        end_time = input_data.get('end_timestamp')
        duration_ms = None
        if start_time and end_time:
            duration_ms = int((end_time - start_time) * 1000)

        # Determine status
        status = 'failed' if error else 'completed'
        error_message = str(error) if error else None

        # Log tool call completion
        if call_id:
            log_tool_call_end(
                call_id=call_id,
                result=result,
                duration_ms=duration_ms,
                status=status,
                error_message=error_message
            )

        # Track file modifications for Write/Edit tools
        if tool_name in ['Write', 'Edit', 'MultiEdit'] and status == 'completed':
            track_file_modification(input_data, call_id)

        # Output empty JSON (no message needed)
        print(json.dumps({}), file=sys.stdout)

    except Exception as e:
        # On any error, allow the operation and log
        error_output = {
            "systemMessage": f"Agent logger error in PostToolUse: {str(e)}"
        }
        print(json.dumps(error_output), file=sys.stdout)

    finally:
        # ALWAYS exit 0
        sys.exit(0)


if __name__ == '__main__':
    main()
