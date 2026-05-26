# LeetCode GitHub Sync

[![CI](https://github.com/ashmitahaldar/leetcode-github-sync/actions/workflows/ci.yml/badge.svg)](https://github.com/ashmitahaldar/leetcode-github-sync/actions/workflows/ci.yml)

A lightweight Python CLI that syncs accepted LeetCode submissions into an existing GitHub repository.

It uses:

- LeetCode GraphQL with your local LeetCode session cookies.
- GitHub API commits using a GitHub token.
- A TOML config file for non-secret settings.
- A git-ignored `.env` file for secrets.

## Table Of Contents

- [How It Works](#how-it-works)
- [Install](#install)
- [Quick Start: Try It Safely](#quick-start-try-it-safely)
- [Configure](#configure)
- [Getting LeetCode Cookies](#getting-leetcode-cookies)
- [Getting A GitHub Token](#getting-a-github-token)
- [Commands](#commands)
- [Repository Output](#repository-output)
- [Behavior](#behavior)
- [Uninstall Or Reset](#uninstall-or-reset)
- [Tests](#tests)

## How It Works

```text
LeetCode GraphQL
      |
      v
Accepted submissions
      |
      v
Sync planner
      |
      v
Generated solution files + metadata
      |
      v
GitHub Commit API
```

The tool reads accepted submissions from LeetCode using your browser session cookies, then compares them against the generated files already present in the configured GitHub repository.

Before writing anything, the sync planner builds a file-level plan: create, update, or skip. `sync --dry-run` prints that plan without creating a commit. A real `sync` uses the GitHub Commit API to write one all-or-nothing commit to the configured branch.

After the first backfill, sync becomes incremental automatically. The tool reads existing `metadata.json` files from the target repository, finds the latest synced `submitted_at_unix`, applies a one-day lookback buffer, and asks LeetCode only for recent submissions. `sync --full-sync` bypasses this optimization when you want a complete rescan.

User-owned notes are protected: `notes.md` is created once if missing, then never overwritten by the tool. Secrets stay local in `.env` and are never written into generated files.

## Install

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

Windows Command Prompt:

```bat
py -m venv .venv
.venv\Scripts\activate.bat
pip install -e ".[dev]"
```

## Quick Start: Try It Safely

Use dry-run mode before writing anything to GitHub.

1. Make sure your target GitHub repository already exists and has a `main` branch.
2. Activate the local environment:

macOS/Linux:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```bat
.venv\Scripts\activate.bat
```

3. Edit `leetcode-sync.toml` with your GitHub owner, repo, and branch.
4. Create `.env`.

macOS/Linux:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Windows Command Prompt:

```bat
copy .env.example .env
```

5. Add your LeetCode cookies and GitHub token to `.env`.
   - Need LeetCode cookies? See [Getting LeetCode Cookies](#getting-leetcode-cookies).
   - Need a GitHub token? See [Getting A GitHub Token](#getting-a-github-token).
6. Check that authentication works:

```bash
leetcode-sync status
```

7. Preview the sync without writing to GitHub:

```bash
leetcode-sync sync --dry-run
```

8. If the preview looks right, run the real sync:

```bash
leetcode-sync sync
```

## Configure

Edit `leetcode-sync.toml`:

```toml
[github]
owner = "your-github-username"
repo = "your-target-repo"
branch = "main"
```

Create `.env` from `.env.example`:

macOS/Linux:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Windows Command Prompt:

```bat
copy .env.example .env
```

Fill in:

- `LEETCODE_SESSION`: your LeetCode session cookie.
- `CSRFTOKEN`: your LeetCode CSRF token, if present.
- `GITHUB_TOKEN`: a GitHub token with read/write contents access to the target repository.

Do not commit `.env`. This project ignores it by default.

## Getting LeetCode Cookies

The CLI reuses your existing browser login. You do not need to type your LeetCode password into this tool.

### Chrome Or Edge

1. Go to [leetcode.com](https://leetcode.com) and make sure you are logged in.
2. Open DevTools:
   - macOS: `Cmd + Option + I`
   - Windows/Linux: `Ctrl + Shift + I`
3. Go to the **Application** tab.
4. In the left sidebar, open **Storage → Cookies → https://leetcode.com**.
5. Find these cookie names:
   - `LEETCODE_SESSION`
   - `csrftoken`
6. Copy their **Value** fields into `.env`:

```bash
LEETCODE_SESSION=paste_the_LEETCODE_SESSION_value_here
CSRFTOKEN=paste_the_csrftoken_value_here
GITHUB_TOKEN=paste_your_github_token_here
```

### Safari

1. Enable developer tools if needed: **Safari → Settings → Advanced → Show features for web developers**.
2. Open LeetCode and make sure you are logged in.
3. Open Web Inspector.
4. Look under storage or cookies for `leetcode.com`.
5. Copy `LEETCODE_SESSION` and `csrftoken` into `.env`.

Treat `LEETCODE_SESSION` like a password. Anyone with it can act as your logged-in LeetCode session. If sync stops working later, your LeetCode session probably expired; copy a fresh cookie value from your browser.

## Getting A GitHub Token

The CLI uses a GitHub token to create commits through the GitHub API.

Use a fine-grained personal access token:

1. Go to [GitHub Personal Access Tokens](https://github.com/settings/personal-access-tokens).
2. Click **Generate new token**.
3. Choose **Fine-grained token**.
4. Set **Repository access** to only your LeetCode sync repository.
5. Under **Repository permissions**, set:
   - **Contents:** Read and write
   - **Metadata:** Read-only
6. Generate the token and copy it.
7. Put it in `.env`:

```bash
GITHUB_TOKEN=github_pat_your_token_here
```

This token does not need Actions, Issues, Pull Requests, Administration, or full account access. Treat it like a password and never commit it.

## Commands

Check setup:

```bash
leetcode-sync status
```

Run full setup diagnostics:

```bash
leetcode-sync doctor
```

Show non-secret config and secret presence:

```bash
leetcode-sync config show
```

Preview changes without writing to GitHub:

```bash
leetcode-sync sync --dry-run
```

Sync accepted submissions:

```bash
leetcode-sync sync
```

After the first backfill, plain `sync` automatically uses repository metadata to fetch only recent submissions, with a one-day lookback buffer.

Sync submissions since a date:

```bash
leetcode-sync sync --since 2026-01-01
```

Force a complete LeetCode rescan:

```bash
leetcode-sync sync --full-sync
```

Create starter local files in another directory:

```bash
leetcode-sync init
```

## Repository Output

Synced files are written to the target GitHub repository like this:

```text
problems/
  0001-two-sum/
    solution.py
    solution.java
    metadata.json
    notes.md
```

`solution.*` and `metadata.json` are generated. `notes.md` is created once and never overwritten.

## Behavior

- Only Accepted submissions are synced.
- The latest accepted submission is kept per problem and language.
- Multiple languages for the same problem are preserved.
- The first sync performs a full backfill; later syncs automatically use `metadata.json` timestamps to reduce LeetCode API calls.
- Re-running sync is idempotent and creates no commit when nothing changed.
- `sync --dry-run` prints planned creates, updates, and skips without writing.
- `sync --full-sync` bypasses incremental mode and scans all accepted submissions.
- `doctor` validates setup and reports actionable failures.
- `config show` prints config and whether secrets are set without printing secret values.
- `sync` and `sync --dry-run` finish with a concise summary showing repo, mode, fetched submissions, planned files, and commit status.
- GitHub writes are all-or-nothing through a single commit.
- Secrets are redacted from error messages.

## Uninstall Or Reset

Local cleanup is manual and non-destructive:

macOS/Linux:

```bash
rm -rf .venv .pytest_cache
rm -f .env
```

Windows PowerShell:

```powershell
Remove-Item -Recurse -Force .venv, .pytest_cache
Remove-Item .env
```

Windows Command Prompt:

```bat
rmdir /s /q .venv
rmdir /s /q .pytest_cache
del .env
```

To remove synced files from GitHub, delete them in the target repository yourself so you can review exactly what will be removed.

## Tests

```bash
pytest
```

Run the full local verification suite:

```bash
ruff check src tests
mypy
pytest
```
