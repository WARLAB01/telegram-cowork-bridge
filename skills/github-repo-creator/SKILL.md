---
name: github-repo-creator
description: Create GitHub repositories and push code from Cowork. Use this skill when users want to create a new repo, push code to GitHub, share a project on git, or upload to GitHub. Handles browser automation for repo creation and knows which tools work for git operations in Cowork's environment.
---

# GitHub Repository Creator Skill

Create GitHub repositories and push code from Cowork with proper tool selection and error handling.

## Overview

This skill handles the complete workflow of creating a GitHub repository and pushing local code. It documents the specific tools that work in the Cowork environment and the pitfalls to avoid.

---

## Key Learnings & Tool Selection

### ⚠️ Critical: Use the Right Tool for Each Task

| Task | ✅ Use This | ❌ Don't Use |
|------|------------|--------------|
| Create project files | Cowork Write/Bash | - |
| Git init/add/commit | Cowork Bash | Desktop Commander |
| Navigate browser to GitHub | Claude in Chrome (own tabs) | Control Chrome (JS fails) |
| Click buttons on GitHub | Claude in Chrome computer tool | Control Chrome execute_javascript |
| Git push to remote | **Desktop Commander** | Cowork Bash (network limited) |
| Check git credentials | Desktop Commander | Cowork Bash |

### Why Desktop Commander for Git Push?

The Cowork VM has network limitations:
- SSH DNS resolution fails: `Could not resolve hostname github.com`
- HTTPS requires credentials not available in VM

Desktop Commander runs directly on the Mac and has access to:
- SSH keys in `~/.ssh/`
- Git credential helpers
- macOS Keychain credentials

---

## Complete Workflow

### Phase 1: Create Project Structure

```
1. Create directory in mounted folder:
   /sessions/[session]/mnt/[folder]/Projects/[repo-name]/

2. Write all project files using Cowork Write tool

3. Initialize git and commit using Cowork Bash:
   cd /sessions/.../Projects/repo-name
   git init
   git config user.email "user@email.com"
   git config user.name "User Name"
   git add -A
   git commit -m "Initial commit"
```

### Phase 2: Create GitHub Repository (Browser)

**Step 2.1: Get Claude in Chrome Tab**
```
mcp__Claude_in_Chrome__tabs_context_mcp
  → Returns available tab IDs

If no tabs or only chrome:// tabs:
  mcp__Claude_in_Chrome__tabs_create_mcp
  → Creates new tab, returns tabId
```

**Step 2.2: Navigate to GitHub New Repo Page**
```
mcp__Claude_in_Chrome__navigate
  tabId: [from step 2.1]
  url: "https://github.com/new?name=[repo-name]&visibility=public"

TIP: The URL parameters pre-fill the form!
  - name=[repo-name] → fills repository name
  - visibility=public → selects public visibility
```

**Step 2.3: Verify Page Loaded & Take Screenshot**
```
mcp__Claude_in_Chrome__computer
  action: "screenshot"
  tabId: [tabId]

→ Verify: Page shows "Create a new repository"
→ Verify: Name field is pre-filled
→ Verify: Shows "[repo-name] is available" in green
```

**Step 2.4: Scroll to Find Create Button**
```
mcp__Claude_in_Chrome__computer
  action: "scroll"
  tabId: [tabId]
  coordinate: [770, 400]
  scroll_direction: "down"
  scroll_amount: 3
```

**Step 2.5: Click Create Repository Button**
```
mcp__Claude_in_Chrome__computer
  action: "left_click"
  tabId: [tabId]
  coordinate: [1036, 631]  # Approximate location

→ Take screenshot to verify repo was created
→ URL should change to: github.com/[username]/[repo-name]
```

### Phase 3: Push Code to GitHub

**Step 3.1: Add Remote (Cowork Bash)**
```bash
cd /sessions/.../Projects/repo-name
git remote add origin git@github.com:[username]/[repo-name].git
```

**Step 3.2: Push Using Desktop Commander** ⚠️ CRITICAL
```
mcp__Desktop_Commander__start_process
  command: "cd ~/Projects/[repo-name] && git push -u origin main 2>&1"
  timeout_ms: 30000

→ This runs on the Mac, not in the VM
→ Has access to SSH keys and credentials
→ Will succeed where Cowork Bash fails
```

---

## Troubleshooting

### "Chrome is not running" from Control Chrome

**Problem:** `mcp__Control_Chrome__execute_javascript` returns this error even though Chrome is open.

**Solution:** Don't use Control Chrome for JavaScript execution. Use Claude in Chrome tools instead:
- Use `mcp__Claude_in_Chrome__navigate` for navigation
- Use `mcp__Claude_in_Chrome__computer` for clicks/screenshots
- Claude in Chrome has its own tab group - create tabs within it

### Claude in Chrome navigate times out

**Problem:** `mcp__Claude_in_Chrome__navigate` times out after 30s.

**Solutions:**
1. Try creating a fresh tab first with `tabs_create_mcp`
2. Use `tabs_context_mcp` to verify tabs exist
3. If persistent, fall back to Control Chrome for opening URL, then use Claude in Chrome for interaction

### Git push fails with "could not read Username"

**Problem:** HTTPS push fails in Cowork Bash.

**Solution:** Use Desktop Commander instead:
```
mcp__Desktop_Commander__start_process
  command: "cd ~/Projects/repo && git push -u origin main"
```

### Git push fails with DNS resolution error

**Problem:** SSH push fails with "Could not resolve hostname github.com".

**Solution:** Same as above - use Desktop Commander which runs on Mac with full network access.

### Git commit fails with "Author identity unknown"

**Problem:** Git needs user config.

**Solution:** Set config before committing:
```bash
git config user.email "user@email.com"
git config user.name "User Name"
```

### Lock file exists error

**Problem:** `.git/index.lock` file prevents operations.

**Solution:**
1. Request delete permission: `mcp__cowork__allow_cowork_file_delete`
2. Remove lock: `rm -f .git/index.lock`

---

## Quick Reference: Tool Capabilities

### Claude in Chrome MCP
- ✅ Navigate to URLs (in its own tabs)
- ✅ Screenshot pages
- ✅ Click at coordinates (`left_click`)
- ✅ Scroll pages
- ✅ Type text
- ✅ Read page content
- ❌ Cannot see tabs opened by Control Chrome

### Control Chrome MCP
- ✅ Open URLs (any tab)
- ✅ List all tabs
- ✅ Switch tabs
- ✅ Get current tab info
- ❌ execute_javascript often fails
- ❌ Tabs not visible to Claude in Chrome

### Desktop Commander MCP
- ✅ Run commands on Mac directly
- ✅ Access to SSH keys and git credentials
- ✅ Full network access
- ✅ Read/write files
- ❌ Different paths than Cowork (use ~/Projects not /sessions/...)

### Cowork Bash
- ✅ Run commands in VM
- ✅ Git init/add/commit
- ✅ File operations in mounted folders
- ❌ Limited network (no SSH to github.com)
- ❌ No git credential access

---

## Example: Complete Repo Creation

```python
# Pseudocode for the complete workflow

# 1. Create project
write_files_to("/sessions/.../mnt/folder/Projects/my-repo/")

# 2. Git init and commit
bash("cd /sessions/.../Projects/my-repo && git init")
bash("git config user.email 'user@email.com'")
bash("git config user.name 'User Name'")
bash("git add -A && git commit -m 'Initial commit'")

# 3. Create GitHub repo via browser
tab_id = claude_chrome.tabs_create_mcp()
claude_chrome.navigate(tab_id, "https://github.com/new?name=my-repo&visibility=public")
claude_chrome.computer("screenshot", tab_id)  # Verify page
claude_chrome.computer("scroll", tab_id, down=3)  # Find button
claude_chrome.computer("left_click", tab_id, [1036, 631])  # Click create
claude_chrome.computer("screenshot", tab_id)  # Verify created

# 4. Add remote (Cowork bash is fine for this)
bash("git remote add origin git@github.com:user/my-repo.git")

# 5. Push via Desktop Commander (CRITICAL!)
desktop_commander.start_process("cd ~/Projects/my-repo && git push -u origin main")
```

---

## Trigger Phrases

Use this skill when the user says:
- "create a github repo"
- "push this to github"
- "put this on git"
- "create a repository"
- "upload to github"
- "share this on github"
- "make a new repo"

---

## Files in This Skill

```
github-repo-creator/
├── SKILL.md          # This file - main documentation
└── templates/
    └── gitignore.txt # Common .gitignore template
```
