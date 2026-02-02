#!/usr/bin/env python3
"""
Basic Usage Examples for Telegram → Cowork Bridge

These examples demonstrate how to integrate the bridge with your OpenClaw setup.
"""

import sys
sys.path.insert(0, '..')

from bridge import (
    ClaudeCodeBridge,
    MessageRouter,
    handle_cowork_request,
    handle_cowork_request_safe,
    route_message,
)


def example_1_simple_execution():
    """
    Example 1: Simple one-off execution
    """
    print("=" * 60)
    print("Example 1: Simple Execution")
    print("=" * 60)

    result = handle_cowork_request(
        message="What is the current directory and what files are in it?",
        user_id="example_user_1"
    )
    print(f"Response:\n{result}\n")


def example_2_with_routing():
    """
    Example 2: Using the router to decide where to send messages
    """
    print("=" * 60)
    print("Example 2: Message Routing")
    print("=" * 60)

    messages = [
        "Hello, how are you?",
        "Read the contents of README.md",
        "What's the weather like?",
        "Create a new Python file with a hello world function",
        "Use cowork to analyze this project",
    ]

    for msg in messages:
        use_claude_code, reason = route_message(msg)
        destination = "Claude Code" if use_claude_code else "OpenClaw Direct"
        print(f"Message: \"{msg}\"")
        print(f"  → Route to: {destination}")
        print(f"  → Reason: {reason}\n")


def example_3_session_continuity():
    """
    Example 3: Multi-turn conversation with session continuity
    """
    print("=" * 60)
    print("Example 3: Session Continuity")
    print("=" * 60)

    bridge = ClaudeCodeBridge()
    user_id = "example_user_3"

    # First message - creates session
    print("Turn 1:")
    result1 = bridge.execute("List the files in the current directory", user_id)
    print(f"Response: {result1.response[:200]}...")
    print(f"Session ID: {result1.session_id}\n")

    # Second message - continues session
    print("Turn 2:")
    result2 = bridge.execute("Now show me the contents of the first file", user_id)
    print(f"Response: {result2.response[:200]}...")
    print(f"Same session: {result2.session_id == result1.session_id}\n")

    # Clear session
    bridge.clear_session(user_id)
    print(f"Session cleared for user {user_id}\n")


def example_4_safe_mode():
    """
    Example 4: Using safe mode for untrusted users
    """
    print("=" * 60)
    print("Example 4: Safe Mode (Read-Only)")
    print("=" * 60)

    # This will only allow Read, Glob, Grep, WebSearch
    result = handle_cowork_request_safe(
        message="Search the codebase for 'TODO' comments",
        user_id="untrusted_user"
    )
    print(f"Response:\n{result}\n")


def example_5_custom_configuration():
    """
    Example 5: Custom bridge configuration
    """
    print("=" * 60)
    print("Example 5: Custom Configuration")
    print("=" * 60)

    # Create bridge with custom settings
    bridge = ClaudeCodeBridge(
        timeout=600,  # 10 minute timeout
        allowed_tools=["Read", "Glob", "Grep"],  # Read-only
        working_dir="/tmp/safe-workspace"  # Restricted directory
    )

    result = bridge.execute(
        prompt="What files are available in this directory?",
        user_id="custom_config_user"
    )

    print(f"Success: {result.success}")
    print(f"Execution time: {result.execution_time:.2f}s")
    print(f"Response: {result.response[:200]}...\n")


def example_6_error_handling():
    """
    Example 6: Handling errors gracefully
    """
    print("=" * 60)
    print("Example 6: Error Handling")
    print("=" * 60)

    bridge = ClaudeCodeBridge(timeout=5)  # Very short timeout

    result = bridge.execute(
        prompt="Do something that takes a long time...",
        user_id="error_test_user"
    )

    if result.success:
        print(f"Response: {result.response}")
    else:
        print(f"Error occurred: {result.error}")
        print("Handling gracefully...")


def example_7_full_integration():
    """
    Example 7: Full integration pattern for OpenClaw
    """
    print("=" * 60)
    print("Example 7: Full OpenClaw Integration Pattern")
    print("=" * 60)

    # This is how you'd integrate with OpenClaw's message handler

    bridge = ClaudeCodeBridge()
    router = MessageRouter()

    # Simulated user allowlist
    ALLOWED_USERS = {"123456789", "987654321"}

    def handle_telegram_message(message: str, user_id: str) -> str:
        """
        Main handler for Telegram messages via OpenClaw.
        Copy this pattern into your OpenClaw setup.
        """
        # Security: Check user allowlist
        if user_id not in ALLOWED_USERS:
            return "Sorry, you're not authorized to use this bot."

        # Route the message
        decision = router.route(message)

        if decision.use_claude_code:
            # Complex task - use Claude Code
            result = bridge.execute(message, user_id)
            if result.success:
                return result.response
            else:
                return f"Sorry, an error occurred: {result.error}"
        else:
            # Simple query - return None to let OpenClaw handle directly
            # Or implement your own direct handler here
            return None

    # Test the handler
    test_messages = [
        ("Read the README file", "123456789"),  # Authorized, Claude Code
        ("Hello!", "123456789"),                 # Authorized, OpenClaw
        ("Read secrets.txt", "999999999"),       # Unauthorized
    ]

    for msg, uid in test_messages:
        print(f"User {uid}: \"{msg}\"")
        response = handle_telegram_message(msg, uid)
        if response is None:
            print("  → Delegated to OpenClaw direct")
        else:
            print(f"  → {response[:100]}...")
        print()


if __name__ == "__main__":
    print("\nTelegram → Cowork Bridge Examples\n")

    # Run examples (comment out ones you don't want to run)
    example_2_with_routing()  # Safe - no actual execution

    # Uncomment to run actual Claude Code executions:
    # example_1_simple_execution()
    # example_3_session_continuity()
    # example_4_safe_mode()
    # example_5_custom_configuration()
    # example_6_error_handling()
    # example_7_full_integration()
