# Security Hardening Guide

## ⚠️ Important Security Considerations

This bridge connects external messaging (Telegram) to Claude Code, which has powerful capabilities including file system access and code execution. **Proper security configuration is essential.**

## Threat Model

### Attack Vectors

1. **Unauthorized Access**: Malicious users messaging your bot
2. **Prompt Injection**: Crafted messages that manipulate Claude Code
3. **Resource Exhaustion**: DoS via expensive/long-running tasks
4. **Data Exfiltration**: Extracting sensitive files via Claude Code
5. **Code Execution**: Running malicious commands via Bash tool

## Security Layers

### Layer 1: User Authentication

**Always restrict who can use your bot.**

```python
# config/routing.json
{
  "user_allowlist": [
    "123456789",    # Your Telegram user ID
    "987654321"     # Trusted team member
  ]
}

# In your handler
ALLOWED_USERS = {"123456789", "987654321"}

def handle_message(message, user_id):
    if user_id not in ALLOWED_USERS:
        return "Unauthorized"
    # ... process message
```

**Getting your Telegram user ID:**
1. Message @userinfobot on Telegram
2. It will reply with your user ID

### Layer 2: Input Sanitization

**Remove dangerous patterns from user input.**

```python
def sanitize_prompt(prompt: str) -> str:
    dangerous_patterns = [
        r'--allowedTools',      # Tool override
        r'--dangerously',       # Safety bypass
        r'-p\s',                # Print flag injection
        r'--resume',            # Session hijack
        r'--output-format',     # Output manipulation
    ]

    sanitized = prompt
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)

    return sanitized
```

### Layer 3: Tool Restrictions

**Limit Claude Code capabilities based on trust level.**

```python
# Trusted users - full access
FULL_TOOLS = ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "WebFetch", "WebSearch"]

# Untrusted users - read-only
SAFE_TOOLS = ["Read", "Glob", "Grep", "WebSearch"]

# Paranoid mode - minimal access
MINIMAL_TOOLS = ["Read", "Glob"]

def get_tools_for_user(user_id: str) -> list:
    if user_id in ADMIN_USERS:
        return FULL_TOOLS
    elif user_id in TRUSTED_USERS:
        return SAFE_TOOLS
    else:
        return MINIMAL_TOOLS
```

### Layer 4: Resource Limits

**Prevent resource exhaustion.**

```python
# Execution timeout
TIMEOUT_SECONDS = 300  # 5 minutes max

# Rate limiting
from collections import defaultdict
import time

rate_limits = defaultdict(list)  # user_id -> [timestamps]

def check_rate_limit(user_id: str, max_per_minute: int = 10) -> bool:
    now = time.time()
    minute_ago = now - 60

    # Clean old entries
    rate_limits[user_id] = [t for t in rate_limits[user_id] if t > minute_ago]

    if len(rate_limits[user_id]) >= max_per_minute:
        return False  # Rate limited

    rate_limits[user_id].append(now)
    return True
```

### Layer 5: Working Directory Isolation

**Restrict file access to specific directories.**

```python
# Only allow access to specific project directory
ALLOWED_WORKING_DIR = "/home/user/projects/safe-workspace"

def execute_safe(prompt: str, user_id: str):
    return bridge.execute(
        prompt=prompt,
        user_id=user_id,
        working_dir=ALLOWED_WORKING_DIR,
        allowed_tools=SAFE_TOOLS
    )
```

### Layer 6: Audit Logging

**Log everything for review.**

```python
import logging
from datetime import datetime

# Configure audit logger
audit_logger = logging.getLogger('audit')
audit_logger.setLevel(logging.INFO)
handler = logging.FileHandler('/var/log/telegram-cowork-bridge/audit.log')
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
))
audit_logger.addHandler(handler)

def log_request(user_id: str, message: str, result: ExecutionResult):
    audit_logger.info(json.dumps({
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "message": message[:500],  # Truncate long messages
        "success": result.success,
        "execution_time": result.execution_time,
        "error": result.error
    }))
```

## Environment Hardening

### Running in Docker (Recommended)

```dockerfile
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -s /bin/bash bridge
USER bridge

# Install dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Copy application
COPY --chown=bridge:bridge . .

# Run with limited capabilities
CMD ["python", "-m", "bridge"]
```

```yaml
# docker-compose.yml
services:
  bridge:
    build: .
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./workspace:/workspace:rw  # Limited directory access
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
```

### System-Level Restrictions

```bash
# Create dedicated user
sudo useradd -r -s /bin/false telegram-bridge

# Restrict directory access
sudo mkdir -p /opt/telegram-bridge/workspace
sudo chown telegram-bridge:telegram-bridge /opt/telegram-bridge/workspace
sudo chmod 700 /opt/telegram-bridge/workspace

# Run with systemd
# /etc/systemd/system/telegram-bridge.service
[Unit]
Description=Telegram Cowork Bridge
After=network.target

[Service]
Type=simple
User=telegram-bridge
Group=telegram-bridge
WorkingDirectory=/opt/telegram-bridge
ExecStart=/usr/bin/python3 -m bridge
Restart=on-failure

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
ReadWritePaths=/opt/telegram-bridge/workspace

[Install]
WantedBy=multi-user.target
```

## Security Checklist

### Before Deployment

- [ ] User allowlist configured
- [ ] Rate limiting enabled
- [ ] Timeouts configured
- [ ] Tool restrictions set appropriately
- [ ] Input sanitization active
- [ ] Audit logging enabled
- [ ] Working directory restricted
- [ ] Running as non-root user
- [ ] Secrets in environment variables (not code)

### Regular Maintenance

- [ ] Review audit logs weekly
- [ ] Rotate API keys monthly
- [ ] Update dependencies regularly
- [ ] Test security controls quarterly
- [ ] Review user allowlist periodically

## Incident Response

### If You Suspect a Breach

1. **Immediately disable the bot**
   ```bash
   systemctl stop telegram-bridge
   ```

2. **Rotate credentials**
   - Telegram bot token
   - Anthropic API key

3. **Review audit logs**
   ```bash
   grep -i "suspicious_pattern" /var/log/telegram-cowork-bridge/audit.log
   ```

4. **Check file system**
   - Look for unexpected files
   - Review modification times

5. **Notify stakeholders**
   - Team members
   - Security team if applicable

## Contact

For security issues, please contact the maintainers directly rather than opening a public issue.
