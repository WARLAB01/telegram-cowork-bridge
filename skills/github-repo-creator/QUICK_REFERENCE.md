# GitHub Repo Creator - Quick Reference

## The Golden Rule

> **Use Desktop Commander for `git push`** - Cowork's VM can't reach GitHub.

---

## 5-Step Workflow

### 1️⃣ Create & Commit (Cowork Bash)
```bash
cd /sessions/.../mnt/[folder]/Projects/[repo]
git init && git add -A
git config user.email "email" && git config user.name "name"
git commit -m "Initial commit"
```

### 2️⃣ Get Browser Tab (Claude in Chrome)
```
mcp__Claude_in_Chrome__tabs_create_mcp
→ Returns tabId
```

### 3️⃣ Create Repo (Claude in Chrome)
```
navigate → https://github.com/new?name=[repo]&visibility=public
screenshot → verify name filled
scroll down → find button
left_click → [1036, 631] → create repo
screenshot → verify created
```

### 4️⃣ Add Remote (Cowork Bash)
```bash
git remote add origin git@github.com:[user]/[repo].git
```

### 5️⃣ Push (Desktop Commander) ⚠️
```
mcp__Desktop_Commander__start_process
  command: "cd ~/Projects/[repo] && git push -u origin main"
  timeout_ms: 30000
```

---

## Tool Cheat Sheet

| Task | Tool | Why |
|------|------|-----|
| Write files | Cowork Write | Direct access |
| Git commit | Cowork Bash | Works in VM |
| Browser nav | Claude in Chrome | Has tab access |
| Browser click | Claude in Chrome computer | Coordinates work |
| **Git push** | **Desktop Commander** | **Has credentials** |

---

## Common Errors → Fixes

| Error | Fix |
|-------|-----|
| "Chrome not running" | Use Claude in Chrome, not Control Chrome |
| Navigate timeout | Create fresh tab first |
| "could not read Username" | Use Desktop Commander |
| DNS resolution failed | Use Desktop Commander |
| index.lock exists | `allow_cowork_file_delete` then `rm -f .git/index.lock` |
| Author identity unknown | Set `git config user.email/name` |

---

## URL Parameters for github.com/new

Pre-fill the form via URL:
```
https://github.com/new?name=my-repo&visibility=public&description=My+project
```

| Param | Values |
|-------|--------|
| name | repo-name |
| visibility | public, private |
| description | URL+encoded+text |
