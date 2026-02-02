"""
Claude Code Bridge for OpenClaw

Provides the core functionality to bridge Telegram (via OpenClaw)
to Claude Code's headless mode for file operations and agentic tasks.
"""

from .claude_code_bridge import (
    ClaudeCodeBridge,
    ExecutionResult,
    SessionInfo,
    get_bridge,
    handle_cowork_request,
    handle_cowork_request_safe,
)

from .routing import (
    MessageRouter,
    RoutingDecision,
    get_router,
    route_message,
)

__all__ = [
    # Bridge
    "ClaudeCodeBridge",
    "ExecutionResult",
    "SessionInfo",
    "get_bridge",
    "handle_cowork_request",
    "handle_cowork_request_safe",
    # Routing
    "MessageRouter",
    "RoutingDecision",
    "get_router",
    "route_message",
]

__version__ = "1.0.0"
