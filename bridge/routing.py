"""
Routing Logic for Telegram → Claude Code Bridge

Determines whether messages should be routed to Claude Code
or handled directly by OpenClaw's default model.
"""

import re
import json
from pathlib import Path
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class RoutingDecision:
    """Result of routing decision"""
    use_claude_code: bool
    reason: str
    confidence: float  # 0.0 to 1.0


class MessageRouter:
    """
    Routes messages between OpenClaw (direct API) and Claude Code.

    Claude Code is better for:
    - File operations (read, write, edit)
    - Code analysis and generation
    - Complex multi-step tasks
    - Tasks requiring tool use (bash, search, etc.)

    OpenClaw direct is better for:
    - Simple Q&A
    - Conversation
    - Quick lookups
    - Non-technical tasks
    """

    # Patterns that strongly indicate Claude Code should be used
    CLAUDE_CODE_PATTERNS = [
        # File operations
        (r'\b(file|folder|directory|path)\b', 0.7),
        (r'\b(read|write|edit|create|delete|modify|update)\s+(the\s+)?(file|code|script)', 0.9),
        (r'\b(save|store)\s+(to|as|in)', 0.6),

        # Code operations
        (r'\b(code|script|program|function|class|module)\b', 0.6),
        (r'\b(analyze|review|check|debug|fix|refactor)\s+(the\s+)?(code|script|bug)', 0.8),
        (r'\b(implement|build|develop|create)\s+(a\s+)?(feature|function|class)', 0.8),

        # Search operations
        (r'\b(search|find|grep|look\s+for)\s+(in\s+)?(the\s+)?(codebase|files|project)', 0.8),
        (r'\bwhere\s+is\b.*\b(defined|used|called)\b', 0.7),

        # Complex tasks
        (r'\b(run|execute|test|build|compile|deploy)\b', 0.7),
        (r'\b(install|setup|configure|init)\b', 0.6),

        # Explicit triggers
        (r'\b(use\s+)?(claude\s+code|cowork)\b', 1.0),
        (r'\b(with\s+)?file\s+access\b', 0.9),
    ]

    # Patterns that indicate OpenClaw should handle directly
    OPENCLAW_PATTERNS = [
        (r'^(hi|hello|hey|good\s+(morning|afternoon|evening))', 0.9),
        (r'\b(what|who|when|where|why|how)\s+(is|are|was|were|do|does|did)\b', 0.5),
        (r'\b(weather|time|date|news)\b', 0.8),
        (r'\b(tell\s+me|explain|describe)\s+(about|what)', 0.4),
        (r'\b(thanks|thank\s+you|bye|goodbye)\b', 0.9),
    ]

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize router with optional custom config.

        Args:
            config_path: Path to routing.json config file
        """
        self.custom_patterns = self._load_config(config_path)

    def _load_config(self, config_path: Optional[str]) -> dict:
        """Load custom routing config if provided"""
        if config_path:
            path = Path(config_path)
            if path.exists():
                with open(path) as f:
                    return json.load(f)
        return {}

    def route(self, message: str) -> RoutingDecision:
        """
        Determine routing for a message.

        Args:
            message: User message text

        Returns:
            RoutingDecision with recommendation
        """
        message_lower = message.lower().strip()

        # Calculate scores for each destination
        claude_code_score = 0.0
        openclaw_score = 0.0

        claude_code_matches = []
        openclaw_matches = []

        # Check Claude Code patterns
        for pattern, weight in self.CLAUDE_CODE_PATTERNS:
            if re.search(pattern, message_lower):
                claude_code_score += weight
                claude_code_matches.append(pattern)

        # Check OpenClaw patterns
        for pattern, weight in self.OPENCLAW_PATTERNS:
            if re.search(pattern, message_lower):
                openclaw_score += weight
                openclaw_matches.append(pattern)

        # Check custom patterns from config
        for pattern in self.custom_patterns.get('claude_code_triggers', []):
            if re.search(pattern, message_lower):
                claude_code_score += 0.7
                claude_code_matches.append(f"custom:{pattern}")

        for pattern in self.custom_patterns.get('always_openclaw', []):
            if re.search(pattern, message_lower):
                openclaw_score += 0.8
                openclaw_matches.append(f"custom:{pattern}")

        # Normalize scores
        total = claude_code_score + openclaw_score
        if total > 0:
            cc_confidence = claude_code_score / total
        else:
            cc_confidence = 0.3  # Default slight bias toward OpenClaw

        # Make decision
        use_claude_code = cc_confidence > 0.5

        # Build reason string
        if use_claude_code:
            reason = f"Matched Claude Code patterns: {', '.join(claude_code_matches[:3])}"
        else:
            if openclaw_matches:
                reason = f"Matched OpenClaw patterns: {', '.join(openclaw_matches[:3])}"
            else:
                reason = "No strong patterns, defaulting to OpenClaw"

        return RoutingDecision(
            use_claude_code=use_claude_code,
            reason=reason,
            confidence=cc_confidence if use_claude_code else (1 - cc_confidence)
        )

    def should_use_claude_code(self, message: str) -> bool:
        """Simple boolean check for routing"""
        return self.route(message).use_claude_code


# ============================================================================
# Convenience functions
# ============================================================================

_router: Optional[MessageRouter] = None


def get_router(config_path: Optional[str] = None) -> MessageRouter:
    """Get or create the global router instance"""
    global _router
    if _router is None:
        _router = MessageRouter(config_path)
    return _router


def route_message(message: str) -> Tuple[bool, str]:
    """
    Route a message and return decision.

    Returns:
        Tuple of (use_claude_code: bool, reason: str)
    """
    decision = get_router().route(message)
    return decision.use_claude_code, decision.reason


# ============================================================================
# CLI for testing
# ============================================================================

if __name__ == "__main__":
    import sys

    test_messages = [
        "Hello, how are you?",
        "Read the contents of main.py",
        "What's the weather like?",
        "Create a new file called test.js with a hello world function",
        "Search the codebase for all usages of UserService",
        "Tell me about Python",
        "Run the tests and fix any failures",
        "Use Claude Code to analyze this project",
        "Thanks for your help!",
        "Edit the config.json to add a new setting",
    ]

    router = MessageRouter()

    print("Routing Test Results")
    print("=" * 60)

    for msg in test_messages:
        decision = router.route(msg)
        dest = "Claude Code" if decision.use_claude_code else "OpenClaw"
        print(f"\nMessage: \"{msg}\"")
        print(f"  → {dest} (confidence: {decision.confidence:.2f})")
        print(f"  Reason: {decision.reason}")
