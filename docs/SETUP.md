# Setup Guide

Complete step-by-step instructions to get the Telegram → Cowork bridge running.

## Prerequisites

### Required Software

1. **Python 3.9+** or **Node.js 18+** (depending on which implementation you use)
2. **Claude Code CLI** installed and authenticated
3. **OpenClaw** installed and configured with Telegram
4. **Git** for version control

### Required Accounts/Keys

1. **Anthropic API Key** - for Claude Code
2. **Telegram Bot Token** - already configured if OpenClaw + Telegram is working

## Step 1: Verify Claude Code Works

First, make sure Claude Code headless mode works on your system:

```bash
# Test basic execution
claude -p "What is 2+2?" --output-format json

# Expected output: JSON with result
```

If this doesn't work:
- Run `claude` to authenticate
- Check your API key: `echo $ANTHROPIC_API_KEY`

## Step 2: Clone and Install

### Python Version

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/telegram-cowork-bridge.git
cd telegram-cowork-bridge

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### TypeScript/Node Version

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/telegram-cowork-bridge.git
cd telegram-cowork-bridge/skill

# Install dependencies
npm install

# Build TypeScript
npm run build
```

## Step 3: Configure the Bridge

### Edit Routing Configuration

```bash
# Edit config/routing.json
nano config/routing.json
```

Key settings to configure:

```json
{
  "user_allowlist": [
    "YOUR_TELEGRAM_USER_ID"
  ],
  "settings": {
    "default_timeout": 300,
    "rate_limit_per_minute": 10
  }
}
```

**Get your Telegram User ID:**
1. Open Telegram
2. Message @userinfobot
3. Copy the ID it returns

### Set Environment Variables

```bash
# Add to ~/.bashrc or ~/.zshrc
export ANTHROPIC_API_KEY="your-key-here"

# Optional: Set working directory
export CLAUDE_CODE_WORKING_DIR="/path/to/your/projects"
```

## Step 4: Integrate with OpenClaw

### Option A: As OpenClaw Skill (Recommended)

```bash
# Copy skill to OpenClaw skills directory
cp -r skill ~/.openclaw/skills/claude-code-bridge

# Edit OpenClaw config
nano ~/.openclaw/openclaw.json
```

Add to your `openclaw.json`:

```json
{
  "skills": {
    "local": [
      "~/.openclaw/skills/claude-code-bridge"
    ]
  }
}
```

### Option B: As Standalone Handler

Modify your OpenClaw message handler to use the bridge:

```python
# In your OpenClaw handler
from bridge import ClaudeCodeBridge, MessageRouter

bridge = ClaudeCodeBridge()
router = MessageRouter()

def handle_telegram_message(message: str, user_id: str) -> str:
    # Check routing
    if router.should_use_claude_code(message):
        result = bridge.execute(message, user_id)
        return result.response if result.success else f"Error: {result.error}"
    else:
        # Let OpenClaw handle directly
        return None  # or your existing handler
```

## Step 5: Test the Integration

### Test Routing Logic

```bash
cd telegram-cowork-bridge
python -m bridge.routing

# Should show routing decisions for test messages
```

### Test Bridge Execution

```bash
python -c "
from bridge import handle_cowork_request
result = handle_cowork_request('What files are in the current directory?', 'test_user')
print(result)
"
```

### Test via Telegram

1. Open Telegram
2. Message your bot with: "use cowork to list files"
3. Should receive a response from Claude Code

## Step 6: Production Deployment

### Running as a Service

```bash
# Create systemd service file
sudo nano /etc/systemd/system/telegram-cowork-bridge.service
```

```ini
[Unit]
Description=Telegram Cowork Bridge
After=network.target

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/path/to/telegram-cowork-bridge
ExecStart=/path/to/venv/bin/python -m bridge
Restart=on-failure
Environment=ANTHROPIC_API_KEY=your-key

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable telegram-cowork-bridge
sudo systemctl start telegram-cowork-bridge

# Check status
sudo systemctl status telegram-cowork-bridge
```

### Running with Docker

```bash
# Build image
docker build -t telegram-cowork-bridge .

# Run container
docker run -d \
  --name telegram-cowork-bridge \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -v /path/to/workspace:/workspace \
  telegram-cowork-bridge
```

## Troubleshooting

### "claude: command not found"

Claude Code CLI is not in PATH:
```bash
# Find claude location
which claude || find / -name "claude" 2>/dev/null

# Add to PATH
export PATH="$PATH:/path/to/claude/directory"
```

### "Authentication required"

Claude Code needs to authenticate:
```bash
claude  # Opens browser for OAuth
```

### "Permission denied" on files

Check working directory permissions:
```bash
ls -la /path/to/working/directory
chmod 755 /path/to/working/directory
```

### Rate limiting errors

Reduce request rate in config:
```json
{
  "settings": {
    "rate_limit_per_minute": 5
  }
}
```

### Timeout errors

Increase timeout for complex tasks:
```python
bridge = ClaudeCodeBridge(timeout=600)  # 10 minutes
```

## Next Steps

1. Review [SECURITY.md](SECURITY.md) for hardening
2. Review [ARCHITECTURE.md](ARCHITECTURE.md) for deep dive
3. Customize routing rules for your use case
4. Set up monitoring and alerting
