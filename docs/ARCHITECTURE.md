# Architecture Documentation

## Overview

This project bridges Telegram messaging (via OpenClaw) to Claude Code's agentic capabilities. The architecture enables users to send messages via Telegram and have complex file/code operations handled by Claude Code running locally.

## System Components

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          User's Machine                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────┐                                                         │
│  │  Telegram  │◄──────────────────────────────────────────────┐        │
│  │    App     │                                                │        │
│  └─────┬──────┘                                                │        │
│        │                                                        │        │
│        │ Messages                                               │        │
│        ▼                                                        │        │
│  ┌──────────────────────────────────────────────────────────┐  │        │
│  │                    OpenClaw Gateway                       │  │        │
│  │  ┌─────────────────────────────────────────────────────┐ │  │        │
│  │  │              Message Router                          │ │  │        │
│  │  │  • Analyzes message intent                          │ │  │        │
│  │  │  • Decides: Claude Code vs Direct API               │ │  │        │
│  │  └──────────────────┬──────────────────────────────────┘ │  │        │
│  │                     │                                     │  │        │
│  │         ┌───────────┴───────────┐                        │  │        │
│  │         │                       │                        │  │        │
│  │         ▼                       ▼                        │  │        │
│  │  ┌─────────────┐      ┌─────────────────────┐           │  │        │
│  │  │ Claude API  │      │ Claude Code Bridge  │           │  │        │
│  │  │  (Direct)   │      │                     │           │  │        │
│  │  │             │      │  subprocess.run()   │           │  │        │
│  │  │ Simple Q&A  │      │  claude -p "..."    │           │  │        │
│  │  │ Conversation│      │                     │           │  │        │
│  │  └──────┬──────┘      └──────────┬──────────┘           │  │        │
│  │         │                        │                       │  │        │
│  └─────────┼────────────────────────┼───────────────────────┘  │        │
│            │                        │                          │        │
│            │                        ▼                          │        │
│            │               ┌────────────────────┐              │        │
│            │               │   Claude Code CLI  │              │        │
│            │               │   (Headless Mode)  │              │        │
│            │               │                    │              │        │
│            │               │  • File System     │              │        │
│            │               │  • Code Execution  │              │        │
│            │               │  • Web Search      │              │        │
│            │               │  • Tool Use        │              │        │
│            │               └─────────┬──────────┘              │        │
│            │                         │                         │        │
│            │                         │ JSON Response           │        │
│            │                         │                         │        │
│            └───────────┬─────────────┘                         │        │
│                        │                                        │        │
│                        │ Formatted Response                     │        │
│                        └────────────────────────────────────────┘        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Message Reception

```
User sends Telegram message
         │
         ▼
OpenClaw receives via Telegram Bot API webhook
         │
         ▼
Message extracted with user_id and text
```

### 2. Routing Decision

```python
# routing.py
decision = router.route(message)

if decision.use_claude_code:
    # File ops, code tasks, complex queries
    result = bridge.execute(message, user_id)
else:
    # Simple Q&A, conversation
    result = openclaw_direct(message, user_id)
```

### 3. Claude Code Execution

```python
# claude_code_bridge.py
cmd = f'claude -p "{prompt}" --output-format json --allowedTools "{tools}"'

# With session continuity
if existing_session:
    cmd += f' --resume {session_id}'

result = subprocess.run(cmd, capture_output=True, timeout=300)
```

### 4. Response Handling

```python
# Parse JSON response
output = json.loads(result.stdout)
response = output.get('result') or output.get('content')

# Update session tracking
sessions[user_id] = SessionInfo(session_id=output['sessionId'], ...)

# Send back via Telegram
telegram_bot.send_message(user_id, response)
```

## Session Management

Sessions enable conversation continuity - users can have multi-turn interactions where Claude Code remembers context.

```python
sessions = {
    "user_123": SessionInfo(
        session_id="abc-def-123",
        started_at=datetime(2024, 1, 15, 10, 30),
        last_activity=datetime(2024, 1, 15, 10, 45),
        message_count=5
    )
}
```

### Session Lifecycle

1. **Creation**: First message from user creates new session
2. **Continuation**: Subsequent messages use `--resume <session_id>`
3. **Expiration**: Sessions cleared after inactivity (configurable)
4. **Manual Clear**: User can request fresh session

## Tool Permissions

Claude Code's capabilities are controlled via `--allowedTools`:

| Tool | Capability | Risk Level |
|------|------------|------------|
| Read | Read files | Low |
| Glob | Find files by pattern | Low |
| Grep | Search file contents | Low |
| WebSearch | Search the web | Low |
| WebFetch | Fetch web pages | Medium |
| Write | Create/overwrite files | High |
| Edit | Modify existing files | High |
| Bash | Execute shell commands | Critical |

### Permission Levels

```python
# Full access (trusted users only)
FULL_TOOLS = ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "WebFetch", "WebSearch"]

# Safe access (untrusted users)
SAFE_TOOLS = ["Read", "Glob", "Grep", "WebSearch"]

# Read-only access
READONLY_TOOLS = ["Read", "Glob", "Grep"]
```

## Error Handling

### Timeout Handling

```python
try:
    result = subprocess.run(cmd, timeout=300)
except subprocess.TimeoutExpired:
    return ExecutionResult(
        success=False,
        error="Task timed out after 5 minutes"
    )
```

### Error Categories

1. **Execution Errors**: Claude Code fails to run
2. **Timeout Errors**: Task exceeds time limit
3. **Permission Errors**: Insufficient tool permissions
4. **Parse Errors**: Invalid JSON response

## Security Model

### Threat Model

| Threat | Mitigation |
|--------|------------|
| Prompt Injection | Sanitize input, remove CLI flags |
| Unauthorized Access | User allowlist |
| Resource Exhaustion | Timeouts, rate limiting |
| Data Exfiltration | Tool restrictions |
| Code Execution | Bash tool restriction for untrusted |

### Defense Layers

1. **Input Sanitization**: Remove dangerous patterns
2. **User Authentication**: Telegram user ID allowlist
3. **Tool Restrictions**: Limit capabilities per user
4. **Execution Sandboxing**: Timeouts, resource limits
5. **Audit Logging**: Log all requests and responses

## Performance Considerations

### Latency Sources

1. Telegram API (50-200ms)
2. OpenClaw processing (10-50ms)
3. Claude Code startup (500-2000ms)
4. LLM inference (1-30s depending on task)
5. Tool execution (varies)

### Optimization Strategies

1. **Session Reuse**: Avoid cold starts with `--resume`
2. **Routing**: Send simple queries to direct API
3. **Caching**: Cache common responses (future)
4. **Parallel Execution**: Handle multiple users concurrently

## Future Enhancements

1. **Streaming Responses**: Send partial results as they arrive
2. **File Attachments**: Handle images, documents from Telegram
3. **Multi-User Workspaces**: Shared project contexts
4. **Scheduled Tasks**: Cron-like automation
5. **Integration Expansion**: Slack, Discord, etc.
