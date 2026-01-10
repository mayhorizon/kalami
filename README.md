# Agent State Management System

A comprehensive logging and state management system for Claude Code that tracks all agent actions, tool calls, and file modifications.

## Features

- **Complete Tool Call Tracking**: Logs every tool invocation with parameters and results
- **Agent Lifecycle Tracking**: Monitors built-in and custom agents from creation to completion
- **File Modification Tracking**: Records all file changes with diffs
- **Automatic Compression**: Compresses large data blobs (> 10KB) using gzip
- **SQLite Storage**: Efficient, serverless database with full-text search capabilities
- **Query CLI**: Easy-to-use command-line interface for querying logs
- **No Performance Impact**: Asynchronous logging that doesn't slow down operations

## Installation

1. Initialize the database:
```bash
python3 db/init_db.py init
```

2. The hooks are already registered in `.claude/hooks.json` and will be automatically loaded by Claude Code on the next session.

## Architecture

```
User Command → Claude Code → Agent Spawned
                ↓
         PreToolUse Hook → Log tool call start
                ↓
         Tool Executes
                ↓
         PostToolUse Hook → Log result + compress if needed
                ↓
         SQLite Database (agent-state.db)
```

## Database Schema

- **sessions**: Tracks Claude Code sessions
- **agents**: Tracks all agents (Explore, Plan, custom, etc.)
- **tool_calls**: Logs every tool invocation with full details
- **modifications**: Records file changes with diffs
- **state_snapshots**: Periodic snapshots of agent/session state

## Usage

### Query CLI

View all sessions:
```bash
python3 cli/query_logs.py sessions
```

List agents in current session:
```bash
python3 cli/query_logs.py agents --session current
```

View tool calls for an agent:
```bash
python3 cli/query_logs.py tools --agent a9bd232
```

View detailed tool call information:
```bash
python3 cli/query_logs.py view-call 12345
```

List file modifications:
```bash
python3 cli/query_logs.py mods --file-path logger.py
```

Export session data:
```bash
python3 cli/query_logs.py export --session current --output session.json
```

Show database statistics:
```bash
python3 cli/query_logs.py stats
```

### Database Management

View database statistics:
```bash
python3 db/init_db.py stats
```

Vacuum database (reclaim space):
```bash
python3 db/init_db.py vacuum
```

Reinitialize database:
```bash
python3 db/init_db.py init
```

## Configuration

Edit `config.json` to customize:

- **compression_threshold_bytes**: Size threshold for compression (default: 10KB)
- **track_builtin_agents**: Enable/disable tracking of Claude Code's built-in agents
- **track_custom_agents**: Enable/disable tracking of custom agents
- **detail_level**: Logging detail level (full, medium, minimal)
- **max_age_days**: Retention period for logs
- **auto_vacuum**: Automatic database vacuuming

## Directory Structure

```
/home/savetheworld/
├── agent-state.db              # SQLite database
├── config.json                 # Configuration file
├── db/
│   ├── schema.sql              # Database schema
│   └── init_db.py              # Database initialization
├── lib/
│   ├── logger.py               # Core logging logic
│   ├── compressor.py           # Compression utilities
│   └── session_tracker.py     # Session/agent tracking
├── hooks/
│   ├── pretooluse.py           # PreToolUse hook
│   └── posttooluse.py          # PostToolUse hook
├── cli/
│   └── query_logs.py           # Query CLI
└── .claude/
    └── hooks.json              # Hook registration
```

## How It Works

### Tool Call Logging

1. **PreToolUse Hook**: When any tool is about to execute, the PreToolUse hook captures:
   - Tool name
   - Parameters
   - Timestamp
   - Session and agent context

2. **Tool Execution**: The tool executes normally (logging doesn't interfere)

3. **PostToolUse Hook**: After execution, the PostToolUse hook captures:
   - Tool result
   - Duration
   - Success/failure status
   - File modifications (for Write/Edit tools)

### Data Compression

- Data larger than 10KB is automatically compressed using gzip
- Compression is transparent - the query CLI automatically decompresses when viewing
- Both compressed and uncompressed data are stored in separate columns for optimal querying

### Session & Agent Tracking

- Sessions are identified by unique IDs (generated or from environment)
- Agents are tracked from creation to completion
- Agent hierarchy is maintained for nested agent operations
- All tool calls are associated with their parent agent/session

## Troubleshooting

### Hooks not working

Check if hooks are enabled:
```bash
cat .claude/hooks.json
```

Verify Python 3 is available:
```bash
python3 --version
```

Check hook execution permissions:
```bash
ls -la hooks/*.py
```

### Database errors

Reinitialize the database:
```bash
rm agent-state.db
python3 db/init_db.py init
```

### View hook errors

Hook errors are logged to stderr. You can check Claude Code's output for any error messages starting with "Agent logger error".

## Performance

The logging system is designed to have minimal performance impact:

- Hooks exit immediately on any error (never block operations)
- Compression is fast (gzip level 6)
- Database writes use connection pooling
- SQLite handles concurrent access automatically

## License

MIT License
