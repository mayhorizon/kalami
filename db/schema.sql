-- Agent State Management Database Schema
-- This database tracks all agent actions, tool calls, and modifications

-- Sessions table: tracks Claude Code sessions
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    user_command TEXT,
    working_directory TEXT,
    metadata_json TEXT
);

-- Agents table: tracks all agents (built-in and custom)
CREATE TABLE IF NOT EXISTS agents (
    agent_id TEXT PRIMARY KEY,
    session_id TEXT,
    agent_name TEXT NOT NULL,
    agent_type TEXT,  -- 'Explore', 'Plan', 'custom', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status TEXT,  -- 'running', 'completed', 'failed'
    prompt TEXT,
    user_command TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- Tool calls table: tracks every tool invocation with parameters and results
CREATE TABLE IF NOT EXISTS tool_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT,
    session_id TEXT,
    tool_name TEXT NOT NULL,
    called_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    parameters_json TEXT,  -- For small parameters (< 10KB)
    parameters_compressed BLOB,  -- For large parameters (compressed)
    result_json TEXT,  -- For small results
    result_compressed BLOB,  -- For large results (compressed)
    is_compressed BOOLEAN DEFAULT 0,
    duration_ms INTEGER,
    status TEXT,  -- 'started', 'completed', 'failed'
    error_message TEXT,
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- State snapshots table: periodic snapshots of agent/session state
CREATE TABLE IF NOT EXISTS state_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    agent_id TEXT,
    snapshot_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    snapshot_type TEXT,  -- 'agent_start', 'agent_end', 'periodic', etc.
    state_json TEXT,
    state_compressed BLOB,
    is_compressed BOOLEAN DEFAULT 0,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

-- Modifications table: tracks file changes and other modifications
CREATE TABLE IF NOT EXISTS modifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_call_id INTEGER,
    agent_id TEXT,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modification_type TEXT,  -- 'file_write', 'file_edit', 'file_delete', etc.
    file_path TEXT,
    old_content_hash TEXT,  -- SHA256 hash of old content
    new_content_hash TEXT,  -- SHA256 hash of new content
    diff_compressed BLOB,  -- Compressed diff of changes
    FOREIGN KEY (tool_call_id) REFERENCES tool_calls(id),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_tool_calls_agent ON tool_calls(agent_id);
CREATE INDEX IF NOT EXISTS idx_tool_calls_session ON tool_calls(session_id);
CREATE INDEX IF NOT EXISTS idx_tool_calls_time ON tool_calls(called_at);
CREATE INDEX IF NOT EXISTS idx_tool_calls_tool ON tool_calls(tool_name);
CREATE INDEX IF NOT EXISTS idx_agents_session ON agents(session_id);
CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(agent_type);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_modifications_agent ON modifications(agent_id);
CREATE INDEX IF NOT EXISTS idx_modifications_file ON modifications(file_path);
CREATE INDEX IF NOT EXISTS idx_modifications_time ON modifications(modified_at);
CREATE INDEX IF NOT EXISTS idx_snapshots_session ON state_snapshots(session_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_agent ON state_snapshots(agent_id);
