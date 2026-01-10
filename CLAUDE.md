# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains an **Agent State Management System** - a comprehensive logging and tracking system for Claude Code that monitors all agent actions, tool calls, and file modifications.

## Development Environment

- Python 3.7+ (required for logging system)
- Node.js via nvm (v24.12.0 installed)
- SQLite3 (bundled with Python)
- Working directory: `/home/savetheworld`

## Architecture

### Core Components

1. **SQLite Database** (`agent-state.db`)
   - Stores all sessions, agents, tool calls, and modifications
   - Automatic compression for large data (> 10KB)
   - Indexed for fast queries

2. **Logging Library** (`lib/`)
   - `logger.py` - Core logging functions
   - `compressor.py` - Data compression utilities
   - `session_tracker.py` - Session/agent context tracking

3. **Claude Code Hooks** (`hooks/`)
   - `pretooluse.py` - Logs tool invocations before execution
   - `posttooluse.py` - Logs results and tracks file modifications
   - Registered in `.claude/hooks.json`

4. **Query CLI** (`cli/query_logs.py`)
   - Command-line interface for viewing logs
   - Supports filtering by session, agent, file, etc.

### How It Works

All tool calls made by Claude Code (including those by agents) are automatically logged:

```
User Command → Claude Code → Agent Spawned
                ↓
         PreToolUse Hook → Log tool call start
                ↓
         Tool Executes
                ↓
         PostToolUse Hook → Log result + modifications
                ↓
         SQLite Database
```

## Common Commands

### Query Logs

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
python3 cli/query_logs.py tools --agent <agent_id>
```

View detailed tool call:
```bash
python3 cli/query_logs.py view-call <call_id>
```

List file modifications:
```bash
python3 cli/query_logs.py mods --file-path <path>
```

Export session data:
```bash
python3 cli/query_logs.py export --session current --output session.json
```

Show database stats:
```bash
python3 cli/query_logs.py stats
```

### Database Management

Initialize database:
```bash
python3 db/init_db.py init
```

View statistics:
```bash
python3 db/init_db.py stats
```

Vacuum database:
```bash
python3 db/init_db.py vacuum
```

## Key Files

- `agent-state.db` - SQLite database with all logs
- `config.json` - Configuration (compression threshold, retention, etc.)
- `db/schema.sql` - Database schema definition
- `lib/logger.py` - Core logging API
- `hooks/pretooluse.py` - Pre-execution hook
- `hooks/posttooluse.py` - Post-execution hook
- `.claude/hooks.json` - Hook registration (enables automatic logging)

## Important Notes

### Automatic Logging
- All tool calls are automatically logged (no manual intervention needed)
- Hooks are registered in `.claude/hooks.json` and load automatically
- Logging never blocks operations - hooks exit immediately on errors

### Data Compression
- Data > 10KB is automatically compressed with gzip
- Compression is transparent when querying
- Configurable threshold in `config.json`

### Performance
- Minimal overhead (hooks are fast and non-blocking)
- SQLite handles concurrent access
- Database can be vacuumed to reclaim space

### Troubleshooting

If hooks aren't working:
1. Verify `.claude/hooks.json` exists with correct paths
2. Check Python 3 is available: `python3 --version`
3. Ensure hook scripts are executable: `ls -la hooks/*.py`
4. Look for error messages in Claude Code output

If database is corrupt:
```bash
rm agent-state.db
python3 db/init_db.py init
```

## Development Workflow

When working in this repository:
1. All your tool calls are automatically logged
2. Query logs to understand agent behavior: `python3 cli/query_logs.py`
3. Export session data for analysis: `python3 cli/query_logs.py export --session current`
4. Check database size periodically: `python3 db/init_db.py stats`

## Configuration

Edit `config.json` to customize:
- `compression_threshold_bytes` - When to compress data (default: 10KB)
- `track_builtin_agents` - Track Explore, Plan agents (default: true)
- `track_custom_agents` - Track custom agents (default: true)
- `max_age_days` - Log retention period (default: 30 days)
