"""
Claude Code Bridge for OpenClaw

A Python module to invoke Claude Code in headless mode from OpenClaw,
enabling Telegram users to access Claude Code's file and agentic capabilities.
"""

import subprocess
import json
import re
import time
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SessionInfo:
    """Track session information for a user"""
    session_id: str
    started_at: datetime
    last_activity: datetime
    message_count: int = 1


@dataclass
class ExecutionResult:
    """Result of a Claude Code execution"""
    success: bool
    response: str
    session_id: Optional[str] = None
    error: Optional[str] = None
    execution_time: float = 0.0


class ClaudeCodeBridge:
    """
    Bridge class to invoke Claude Code headless mode from OpenClaw.

    Handles session management, prompt sanitization, and response parsing.
    """

    DEFAULT_TOOLS = [
        "Read", "Write", "Edit", "Bash",
        "Glob", "Grep", "WebFetch", "WebSearch"
    ]

    # Tools that should be restricted for untrusted users
    DANGEROUS_TOOLS = ["Bash", "Write", "Edit"]
    SAFE_TOOLS = ["Read", "Glob", "Grep", "WebSearch"]

    def __init__(
        self,
        timeout: int = 300,
        allowed_tools: Optional[List[str]] = None,
        working_dir: Optional[str] = None
    ):
        """
        Initialize the Claude Code Bridge.

        Args:
            timeout: Execution timeout in seconds (default: 300)
            allowed_tools: List of allowed tools (default: all)
            working_dir: Default working directory for file operations
        """
        self.timeout = timeout
        self.allowed_tools = allowed_tools or self.DEFAULT_TOOLS
        self.working_dir = working_dir
        self.sessions: Dict[str, SessionInfo] = {}

    def sanitize_prompt(self, prompt: str) -> str:
        """
        Sanitize user prompt to prevent injection attacks.

        Args:
            prompt: Raw user prompt

        Returns:
            Sanitized prompt safe for shell execution
        """
        # Remove potential CLI flag injections
        dangerous_patterns = [
            r'--allowedTools',
            r'--dangerously',
            r'-p\s',
            r'--print',
            r'--output-format',
            r'--resume',
            r'--continue',
        ]

        sanitized = prompt
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)

        return sanitized

    def escape_for_shell(self, text: str) -> str:
        """Escape text for safe shell execution"""
        return text.replace('\\', '\\\\').replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')

    def execute(
        self,
        prompt: str,
        user_id: str,
        new_session: bool = False,
        working_dir: Optional[str] = None,
        allowed_tools: Optional[List[str]] = None,
        system_prompt: Optional[str] = None
    ) -> ExecutionResult:
        """
        Execute a prompt via Claude Code headless mode.

        Args:
            prompt: The task/question to send to Claude Code
            user_id: User identifier for session tracking
            new_session: Start a fresh session (default: False)
            working_dir: Working directory override
            allowed_tools: Tool allowlist override
            system_prompt: Additional system prompt to append

        Returns:
            ExecutionResult with response or error
        """
        start_time = time.time()

        # Sanitize and escape prompt
        clean_prompt = self.sanitize_prompt(prompt)
        escaped_prompt = self.escape_for_shell(clean_prompt)

        # Determine tools
        tools = allowed_tools or self.allowed_tools
        tools_arg = f'--allowedTools "{",".join(tools)}"'

        # Build command
        cmd = f'claude -p "{escaped_prompt}" --output-format json {tools_arg}'

        # Add system prompt if provided
        if system_prompt:
            escaped_sys = self.escape_for_shell(system_prompt)
            cmd += f' --append-system-prompt "{escaped_sys}"'

        # Handle session continuity
        if user_id in self.sessions and not new_session:
            session = self.sessions[user_id]
            cmd += f' --resume {session.session_id}'

        # Set working directory
        cwd = working_dir or self.working_dir

        logger.info(f"Executing Claude Code for user {user_id}")
        logger.debug(f"Command: {cmd}")

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=cwd
            )

            execution_time = time.time() - start_time

            if result.returncode == 0:
                # Try to parse JSON output
                try:
                    output = json.loads(result.stdout)
                    response = output.get('result') or output.get('content') or output.get('response') or result.stdout
                    session_id = output.get('sessionId') or output.get('session_id')
                except json.JSONDecodeError:
                    response = result.stdout
                    session_id = None

                # Update session tracking
                if session_id:
                    now = datetime.now()
                    if user_id in self.sessions:
                        self.sessions[user_id].session_id = session_id
                        self.sessions[user_id].last_activity = now
                        self.sessions[user_id].message_count += 1
                    else:
                        self.sessions[user_id] = SessionInfo(
                            session_id=session_id,
                            started_at=now,
                            last_activity=now
                        )

                logger.info(f"Completed in {execution_time:.2f}s for user {user_id}")

                return ExecutionResult(
                    success=True,
                    response=response,
                    session_id=session_id,
                    execution_time=execution_time
                )
            else:
                logger.error(f"Claude Code returned non-zero: {result.stderr}")
                return ExecutionResult(
                    success=False,
                    response="",
                    error=result.stderr or "Command failed",
                    execution_time=execution_time
                )

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            logger.error(f"Execution timed out after {execution_time:.2f}s")
            return ExecutionResult(
                success=False,
                response="",
                error=f"Execution timed out after {self.timeout} seconds",
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = time.time() - start_time
            logger.exception(f"Unexpected error: {e}")
            return ExecutionResult(
                success=False,
                response="",
                error=str(e),
                execution_time=execution_time
            )

    def execute_safe(
        self,
        prompt: str,
        user_id: str,
        **kwargs
    ) -> ExecutionResult:
        """
        Execute with restricted tool set (no Write/Edit/Bash).

        Use this for untrusted users or when you want read-only access.
        """
        return self.execute(
            prompt=prompt,
            user_id=user_id,
            allowed_tools=self.SAFE_TOOLS,
            **kwargs
        )

    def get_session(self, user_id: str) -> Optional[SessionInfo]:
        """Get session info for a user"""
        return self.sessions.get(user_id)

    def clear_session(self, user_id: str) -> bool:
        """Clear session for a user"""
        if user_id in self.sessions:
            del self.sessions[user_id]
            return True
        return False

    def list_sessions(self) -> Dict[str, SessionInfo]:
        """List all active sessions"""
        return self.sessions.copy()


# ============================================================================
# Convenience functions for OpenClaw integration
# ============================================================================

# Global bridge instance
_bridge: Optional[ClaudeCodeBridge] = None


def get_bridge() -> ClaudeCodeBridge:
    """Get or create the global bridge instance"""
    global _bridge
    if _bridge is None:
        _bridge = ClaudeCodeBridge()
    return _bridge


def handle_cowork_request(message: str, user_id: str) -> str:
    """
    Simple handler for OpenClaw integration.

    Args:
        message: User message from Telegram
        user_id: Telegram user ID

    Returns:
        Response string to send back
    """
    bridge = get_bridge()
    result = bridge.execute(message, user_id)

    if result.success:
        return result.response
    else:
        return f"Error: {result.error}"


def handle_cowork_request_safe(message: str, user_id: str) -> str:
    """
    Safe handler (read-only tools) for OpenClaw integration.
    """
    bridge = get_bridge()
    result = bridge.execute_safe(message, user_id)

    if result.success:
        return result.response
    else:
        return f"Error: {result.error}"


# ============================================================================
# CLI for testing
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python claude_code_bridge.py <prompt>")
        sys.exit(1)

    prompt = " ".join(sys.argv[1:])
    result = handle_cowork_request(prompt, "test_user")
    print(result)
