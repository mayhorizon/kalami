# State Management & Logging System Implementation Plan

## Overview
Create a comprehensive state management database using SQLite with JSON compression to track all agent actions, tool calls, and modifications in Claude Code sessions.

## Architecture

### Components
1. **SQLite Database** (`/home/savetheworld/agent-state.db`)
2. **Custom Claude Code Hooks** (PreToolUse & PostToolUse)
3. **Logging Library** (Python module for database operations)
4. **Query Interface** (CLI tool to view logs)
5. **Compression Utilities** (gzip for large JSON blobs)

### Data Flow
```
User Command → Claude Code → Agent Spawned
                ↓
         PreToolUse Hook → Log tool call (start)
                ↓
         Tool Executes
                ↓
         PostToolUse Hook → Log result + compress if needed
                ↓
         SQLite Database (agent-state.db)
```

## Database Schema

### Tables

**1. sessions**
```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    user_command TEXT,
    working_directory TEXT,
    metadata_json TEXT
);
```

**2. agents**
```sql
CREATE TABLE agents (
    agent_id TEXT PRIMARY KEY,
    session_id TEXT,
    agent_name TEXT NOT NULL,
    agent_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status TEXT,
    prompt TEXT,
    user_command TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
```

**3. tool_calls**
```sql
CREATE TABLE tool_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT,
    session_id TEXT,
    tool_name TEXT NOT NULL,
    called_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    parameters_json TEXT,
    parameters_compressed BLOB,
    result_json TEXT,
    result_compressed BLOB,
    is_compressed BOOLEAN DEFAULT 0,
    duration_ms INTEGER,
    status TEXT,
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
```

**4. state_snapshots**
```sql
CREATE TABLE state_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    agent_id TEXT,
    snapshot_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    snapshot_type TEXT,
    state_json TEXT,
    state_compressed BLOB,
    is_compressed BOOLEAN DEFAULT 0,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);
```

**5. modifications**
```sql
CREATE TABLE modifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_call_id INTEGER,
    agent_id TEXT,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modification_type TEXT,
    file_path TEXT,
    old_content_hash TEXT,
    new_content_hash TEXT,
    diff_compressed BLOB,
    FOREIGN KEY (tool_call_id) REFERENCES tool_calls(id),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);
```

### Indexes
```sql
CREATE INDEX idx_tool_calls_agent ON tool_calls(agent_id);
CREATE INDEX idx_tool_calls_session ON tool_calls(session_id);
CREATE INDEX idx_tool_calls_time ON tool_calls(called_at);
CREATE INDEX idx_agents_session ON agents(session_id);
CREATE INDEX idx_modifications_agent ON modifications(agent_id);
CREATE INDEX idx_modifications_file ON modifications(file_path);
```

## Implementation Steps

### Phase 1: Database Setup
**Files to create:**
- `/home/savetheworld/db/schema.sql` - Database schema
- `/home/savetheworld/db/init_db.py` - Database initialization script

**Tasks:**
1. Create SQLite database with schema
2. Add compression threshold configuration (compress if > 10KB)
3. Implement database connection pooling
4. Add database migration support

### Phase 2: Logging Library
**Files to create:**
- `/home/savetheworld/lib/logger.py` - Main logging module
- `/home/savetheworld/lib/compressor.py` - Compression utilities
- `/home/savetheworld/lib/session_tracker.py` - Session management

**Core Functions:**
```python
# logger.py
def log_tool_call_start(agent_id, session_id, tool_name, parameters)
def log_tool_call_end(call_id, result, duration_ms)
def log_agent_start(agent_id, agent_name, prompt, user_command)
def log_agent_end(agent_id, status)
def log_modification(tool_call_id, mod_type, file_path, old_content, new_content)
def create_snapshot(session_id, agent_id, state)

# compressor.py
def compress_if_large(data, threshold=10240) # 10KB
def decompress_data(compressed_blob)
def should_compress(data_size)
```

### Phase 3: Claude Code Hooks Integration
**Files to create:**
- `/home/savetheworld/hooks/pretooluse.py` - PreToolUse hook
- `/home/savetheworld/hooks/posttooluse.py` - PostToolUse hook
- `/home/savetheworld/hooks/hooks.json` - Hook configuration

**Hook Structure:**

**pretooluse.py:**
```python
import json, sys, os
sys.path.insert(0, '/home/savetheworld/lib')
from logger import log_tool_call_start, get_current_session, get_current_agent

def main():
    input_data = json.load(sys.stdin)
    tool_name = input_data.get('tool_name')
    parameters = input_data.get('parameters', {})

    session_id = get_current_session()
    agent_id = get_current_agent()

    # Log tool call start
    call_id = log_tool_call_start(agent_id, session_id, tool_name, parameters)

    # Store call_id for PostToolUse
    print(json.dumps({"call_id": call_id}))
    sys.exit(0)
```

**posttooluse.py:**
```python
import json, sys, os
sys.path.insert(0, '/home/savetheworld/lib')
from logger import log_tool_call_end, log_modification

def main():
    input_data = json.load(sys.stdin)
    tool_name = input_data.get('tool_name')
    result = input_data.get('result', {})
    call_id = input_data.get('call_id')  # from PreToolUse

    # Log tool call result
    log_tool_call_end(call_id, result, duration_ms)

    # Track modifications for Write/Edit tools
    if tool_name in ['Write', 'Edit', 'MultiEdit']:
        track_file_modification(input_data)

    print(json.dumps({}))
    sys.exit(0)
```

**hooks.json:**
```json
{
  "hooks": [
    {
      "name": "agent-logger-pre",
      "event": "PreToolUse",
      "script": "./hooks/pretooluse.py",
      "enabled": true
    },
    {
      "name": "agent-logger-post",
      "event": "PostToolUse",
      "script": "./hooks/posttooluse.py",
      "enabled": true
    }
  ]
}
```

### Phase 4: Session & Agent Tracking
**Files to create:**
- `/home/savetheworld/lib/session_tracker.py`

**Tracking Strategy:**
1. Detect session start via environment variables or `.claude/session-env`
2. Parse agent information from Claude Code's task system
3. Maintain in-memory cache of current session/agent context
4. Read from `.claude/history.jsonl` for historical data

### Phase 5: Query Interface
**Files to create:**
- `/home/savetheworld/cli/query_logs.py` - CLI tool for querying logs

**Features:**
```bash
# View all agents in current session
python3 cli/query_logs.py agents --session current

# View all tool calls for an agent
python3 cli/query_logs.py tools --agent a9bd232

# View all modifications
python3 cli/query_logs.py mods --file-path /path/to/file

# View compressed data (auto-decompresses)
python3 cli/query_logs.py view-call 12345

# Export session data
python3 cli/query_logs.py export --session current --format json
```

### Phase 6: Testing & Validation
**Files to create:**
- `/home/savetheworld/tests/test_logger.py`
- `/home/savetheworld/tests/test_compression.py`
- `/home/savetheworld/tests/test_hooks.py`

## Integration with Claude Code

### Hook Registration
Claude Code reads hooks from:
1. Project-level: `/home/savetheworld/.claude/hooks.json`
2. User-level: `~/.claude/hooks.json`

We'll register at project level to keep it repository-specific.

### Detecting Agents
Claude Code spawns agents via the Task tool. We can detect:
- Agent ID from task system
- Agent type (Explore, Plan, custom)
- Agent name for custom agents

### Session Identification
- Read from `$CLAUDE_SESSION_ID` environment variable (if available)
- Or generate from `.claude/history.jsonl` entries
- Or create new session ID on first hook call

## Compression Strategy

**When to compress:**
- Parameters/results > 10KB
- Store both compressed and threshold marker

**Compression format:**
```python
import gzip, json

def compress_json(data):
    json_bytes = json.dumps(data).encode('utf-8')
    if len(json_bytes) > 10240:  # 10KB
        return gzip.compress(json_bytes), True
    return json_bytes, False
```

**Query optimization:**
- Store small data in JSON columns for easy querying
- Store large data in BLOB columns (compressed)
- Flag indicates which column to read

## File Structure

```
/home/savetheworld/
├── agent-state.db              # SQLite database
├── db/
│   ├── schema.sql
│   └── init_db.py
├── lib/
│   ├── __init__.py
│   ├── logger.py
│   ├── compressor.py
│   └── session_tracker.py
├── hooks/
│   ├── pretooluse.py
│   ├── posttooluse.py
│   └── hooks.json
├── cli/
│   ├── __init__.py
│   └── query_logs.py
├── tests/
│   ├── test_logger.py
│   ├── test_compression.py
│   └── test_hooks.py
├── requirements.txt
└── README.md
```

## Configuration

**config.json:**
```json
{
  "database": {
    "path": "/home/savetheworld/agent-state.db",
    "compression_threshold_bytes": 10240
  },
  "logging": {
    "enabled": true,
    "track_builtin_agents": true,
    "track_custom_agents": true,
    "detail_level": "full"
  }
}
```

## Key Challenges & Solutions

### Challenge 1: Capturing Agent Context
**Problem:** Claude Code doesn't pass agent_id directly to hooks
**Solution:**
- Parse from environment variables
- Read task output files in `/tmp/claude/*/tasks/*.output`
- Track agent lifecycle via tool patterns

### Challenge 2: Concurrent Agent Operations
**Problem:** Multiple agents may run simultaneously
**Solution:**
- Use SQLite's built-in locking
- Add timestamps for ordering
- Store thread/process IDs if available

### Challenge 3: Hook Performance
**Problem:** Logging shouldn't slow down operations
**Solution:**
- Async logging (write to queue, process in background)
- Minimal synchronous work in hooks
- Batch database writes

### Challenge 4: Large Data Volumes
**Problem:** Logs can grow very large
**Solution:**
- Automatic compression for large blobs
- Retention policies (configurable)
- Database vacuuming/cleanup scripts

## Dependencies

```txt
# requirements.txt
# No external dependencies needed - uses Python stdlib only
```

## Execution Order

1. Create database schema
2. Implement logging library
3. Implement compression utilities
4. Create hooks (PreToolUse, PostToolUse)
5. Register hooks with Claude Code
6. Implement session/agent tracking
7. Create query CLI
8. Test with simple tool calls
9. Test with agent spawning
10. Verify compression works
11. Test query interface

## Critical Files

- `/home/savetheworld/db/schema.sql` - Database structure
- `/home/savetheworld/lib/logger.py` - Core logging logic
- `/home/savetheworld/hooks/pretooluse.py` - Tool call start logging
- `/home/savetheworld/hooks/posttooluse.py` - Tool call result logging
- `/home/savetheworld/.claude/hooks.json` - Hook registration
- `/home/savetheworld/cli/query_logs.py` - Query interface

## Success Criteria

1. ✓ All tool calls are logged with timestamps
2. ✓ Agent information is captured (name, type, user command)
3. ✓ File modifications are tracked with diffs
4. ✓ Large data is automatically compressed
5. ✓ Query interface works for common use cases
6. ✓ No performance degradation in Claude Code operations
7. ✓ Both built-in and custom agents are tracked
