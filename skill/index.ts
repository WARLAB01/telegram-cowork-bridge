import { exec, ChildProcess } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

// ============================================================================
// Types
// ============================================================================

interface ClaudeCodeResult {
  success: boolean;
  output: string;
  sessionId?: string;
  error?: string;
  executionTime?: number;
}

interface ExecuteOptions {
  newSession?: boolean;
  workingDir?: string;
  allowedTools?: string[];
  timeout?: number;
  appendSystemPrompt?: string;
}

interface SessionInfo {
  sessionId: string;
  startedAt: Date;
  lastActivity: Date;
  messageCount: number;
}

// ============================================================================
// Session Management
// ============================================================================

const sessions: Map<string, SessionInfo> = new Map();
const activeProcesses: Map<string, ChildProcess> = new Map();

const DEFAULT_TOOLS = [
  "Read", "Write", "Edit", "Bash",
  "Glob", "Grep", "WebFetch", "WebSearch"
];

const DEFAULT_TIMEOUT = 300000; // 5 minutes
const MAX_BUFFER = 10 * 1024 * 1024; // 10MB

// ============================================================================
// Utility Functions
// ============================================================================

function escapeForShell(str: string): string {
  return str
    .replace(/\\/g, '\\\\')
    .replace(/"/g, '\\"')
    .replace(/\$/g, '\\$')
    .replace(/`/g, '\\`')
    .replace(/!/g, '\\!');
}

function sanitizePrompt(prompt: string): string {
  // Remove any potential injection attempts
  const sanitized = prompt
    .replace(/--allowedTools/gi, '')
    .replace(/--dangerously/gi, '')
    .replace(/-p\s/gi, '');
  return sanitized;
}

// ============================================================================
// Core Execution Function
// ============================================================================

export async function claude_code_execute(
  prompt: string,
  userId: string,
  options: ExecuteOptions = {}
): Promise<ClaudeCodeResult> {
  const startTime = Date.now();

  // Sanitize input
  const cleanPrompt = sanitizePrompt(prompt);

  // Determine tools to use
  const tools = options.allowedTools || DEFAULT_TOOLS;
  const toolsArg = `--allowedTools "${tools.join(",")}"`;

  // Build base command
  let cmd = `claude -p "${escapeForShell(cleanPrompt)}" --output-format json ${toolsArg}`;

  // Add system prompt if provided
  if (options.appendSystemPrompt) {
    cmd += ` --append-system-prompt "${escapeForShell(options.appendSystemPrompt)}"`;
  }

  // Handle session continuity
  const existingSession = sessions.get(userId);
  if (existingSession && !options.newSession) {
    cmd += ` --resume ${existingSession.sessionId}`;
  }

  // Execution options
  const execOptions: any = {
    maxBuffer: MAX_BUFFER,
    timeout: options.timeout || DEFAULT_TIMEOUT,
    env: {
      ...process.env,
      // Ensure Claude Code uses JSON output
      CLAUDE_CODE_OUTPUT_FORMAT: 'json'
    }
  };

  // Set working directory if specified
  if (options.workingDir) {
    execOptions.cwd = options.workingDir;
  }

  try {
    console.log(`[claude-code-bridge] Executing for user ${userId}`);

    const { stdout, stderr } = await execAsync(cmd, execOptions);

    // Try to parse JSON output
    let result: any;
    try {
      result = JSON.parse(stdout);
    } catch {
      // If not JSON, use raw output
      result = { content: stdout };
    }

    // Update session tracking
    const sessionId = result.sessionId || result.session_id;
    if (sessionId) {
      const now = new Date();
      if (sessions.has(userId)) {
        const session = sessions.get(userId)!;
        session.lastActivity = now;
        session.messageCount++;
        session.sessionId = sessionId;
      } else {
        sessions.set(userId, {
          sessionId,
          startedAt: now,
          lastActivity: now,
          messageCount: 1
        });
      }
    }

    const executionTime = Date.now() - startTime;
    console.log(`[claude-code-bridge] Completed in ${executionTime}ms`);

    return {
      success: true,
      output: result.result || result.content || result.response || stdout,
      sessionId,
      executionTime
    };

  } catch (error: any) {
    const executionTime = Date.now() - startTime;
    console.error(`[claude-code-bridge] Error after ${executionTime}ms:`, error.message);

    return {
      success: false,
      output: "",
      error: error.message || "Claude Code execution failed",
      executionTime
    };
  }
}

// ============================================================================
// Status & Control Functions
// ============================================================================

export function claude_code_status(userId: string): SessionInfo | null {
  return sessions.get(userId) || null;
}

export function claude_code_cancel(userId: string): boolean {
  const process = activeProcesses.get(userId);
  if (process) {
    process.kill('SIGTERM');
    activeProcesses.delete(userId);
    return true;
  }
  return false;
}

export function claude_code_clear_session(userId: string): boolean {
  return sessions.delete(userId);
}

// ============================================================================
// OpenClaw Skill Export
// ============================================================================

export default {
  name: "claude-code-bridge",
  version: "1.0.0",

  tools: {
    claude_code_execute: {
      description: "Execute a task using Claude Code with file system access and agentic capabilities",
      parameters: {
        prompt: {
          type: "string",
          description: "The task or question to send to Claude Code",
          required: true
        },
        userId: {
          type: "string",
          description: "User ID for session tracking",
          required: true
        },
        newSession: {
          type: "boolean",
          description: "Start a fresh session (default: false)"
        },
        workingDir: {
          type: "string",
          description: "Working directory path for file operations"
        },
        allowedTools: {
          type: "array",
          description: "List of tools to enable (default: Read,Write,Edit,Bash,Glob,Grep,WebFetch,WebSearch)"
        },
        timeout: {
          type: "number",
          description: "Timeout in milliseconds (default: 300000)"
        }
      },
      handler: claude_code_execute
    },

    claude_code_status: {
      description: "Get the current session status for a user",
      parameters: {
        userId: {
          type: "string",
          description: "User ID to check",
          required: true
        }
      },
      handler: claude_code_status
    },

    claude_code_cancel: {
      description: "Cancel an active Claude Code execution",
      parameters: {
        userId: {
          type: "string",
          description: "User ID whose execution to cancel",
          required: true
        }
      },
      handler: claude_code_cancel
    },

    claude_code_clear_session: {
      description: "Clear the session for a user (start fresh next time)",
      parameters: {
        userId: {
          type: "string",
          description: "User ID whose session to clear",
          required: true
        }
      },
      handler: claude_code_clear_session
    }
  }
};
