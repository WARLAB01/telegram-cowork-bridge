# Telegram → Cowork Bridge

A bridge to connect Telegram (via OpenClaw) to Claude Code/Cowork for advanced file operations and agentic tasks.

## Overview

This project enables a flow where:

```
Telegram User → OpenClaw Gateway → Claude Code Headless → Response back to Telegram
```

Since **Cowork** and **Claude Code** share the same engine, we leverage Claude Code's **headless mode** (`claude -p`) as the programmatic bridge point.

## Architecture

```
┌──────────┐      ┌──────────────┐      ┌─────────────────┐
│ Telegram │ ──── │   OpenClaw   │ ──── │  Claude Code    │
│   User   │      │   Gateway    │      │  Headless (-p)  │
└──────────┘      └──────────────┘      └─────────────────┘
     │                   │                       │
     │            ┌──────┴──────┐               │
     │            │             │               │
     │     Simple queries   Complex tasks       │
     │            │             │               │
     │            ▼             ▼               │
     │      ┌─────────┐  ┌───────────┐         │
     │      │ Claude  │  │ Route to  │─────────┘
     │      │   API   │  │ CC Bridge │
     │      └─────────┘  └───────────┘
     │
     └─────────────── Response ◄──────────────────
```

## Prerequisites

- OpenClaw installed and configured with Telegram channel
- Claude Code CLI installed (`claude` command available)
- Node.js 18+ (for TypeScript skill) OR Python 3.9+ (for Python bridge)
- Anthropic API key configured

## Quick Start

### Option 1: OpenClaw Skill (Recommended)

```bash
# Copy the skill to your OpenClaw skills directory
cp -r skill ~/.openclaw/skills/claude-code-bridge

# Install dependencies
cd ~/.openclaw/skills/claude-code-bridge
npm install

# Add to your OpenClaw config
# Edit ~/.openclaw/openclaw.json and add the skill path
```

### Option 2: Python Bridge

```bash
# Install dependencies
pip install -r requirements.txt

# Use the bridge in your OpenClaw handler
from bridge.claude_code_bridge import ClaudeCodeBridge
bridge = ClaudeCodeBridge()
result = bridge.execute("your prompt", "user_id")
```

## Configuration

### Environment Variables

```bash
# Required
export ANTHROPIC_API_KEY="your-key"

# Optional
export CLAUDE_CODE_TIMEOUT=300        # Timeout in seconds (default: 300)
export CLAUDE_CODE_ALLOWED_TOOLS="Read,Write,Edit,Bash,Glob,Grep"
```

### Routing Configuration

Edit `config/routing.json` to define when messages should be routed to Claude Code vs handled directly by OpenClaw:

```json
{
  "claude_code_triggers": [
    "file|folder|directory",
    "create|write|edit|modify",
    "code|script|program",
    "analyze|review|check"
  ],
  "always_openclaw": [
    "weather",
    "time",
    "simple question"
  ]
}
```

## Security

⚠️ **Important Security Considerations:**

1. **User Allowlist**: Only allow specific Telegram user IDs
2. **Tool Restrictions**: Limit available tools for untrusted users
3. **Sandboxing**: Consider running Claude Code in a container/VM
4. **Rate Limiting**: Implement cooldowns to prevent abuse
5. **Audit Logging**: Log all commands for review

See [SECURITY.md](docs/SECURITY.md) for detailed security hardening guide.

## Project Structure

```
telegram-cowork-bridge/
├── README.md
├── docs/
│   ├── ARCHITECTURE.md      # Detailed architecture docs
│   ├── SECURITY.md          # Security hardening guide
│   └── SETUP.md             # Step-by-step setup guide
├── skill/                   # OpenClaw TypeScript skill
│   ├── skill.json
│   ├── index.ts
│   ├── package.json
│   └── tsconfig.json
├── bridge/                  # Python bridge alternative
│   ├── claude_code_bridge.py
│   └── routing.py
├── config/
│   └── routing.json
└── examples/
    └── basic_usage.py
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Related Projects

- [OpenClaw](https://github.com/openclaw/openclaw) - Personal AI assistant
- [clawd-mcp](https://github.com/sandraschi/clawd-mcp) - MCP bridge for OpenClaw
- [Claude Code](https://claude.ai/code) - Anthropic's agentic coding tool
