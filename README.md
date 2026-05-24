# LeetCode GitHub Sync

[![CI](https://github.com/ashmitahaldar/leetcode-github-sync/actions/workflows/ci.yml/badge.svg)](https://github.com/ashmitahaldar/leetcode-github-sync/actions/workflows/ci.yml)

A lightweight Python CLI that syncs accepted LeetCode submissions into an existing GitHub repository.

It uses:

- LeetCode GraphQL with your local LeetCode session cookies.
- GitHub API commits using a GitHub token.
- A TOML config file for non-secret settings.
- A git-ignored `.env` file for secrets.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Quick Start: Try It Safely

Use dry-run mode before writing anything to GitHub.

1. Make sure your target GitHub repository already exists and has a `main` branch.
2. Activate the local environment:

```bash
source .venv/bin/activate
```

3. Edit `leetcode-sync.toml` with your GitHub owner, repo, and branch.
4. Create `.env`:

```bash
cp .env.example .env
```

5. Add your LeetCode cookies and GitHub token to `.env`.
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

```bash
cp .env.example .env
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
2. Open DevTools with `Cmd + Option + I`.
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

Preview changes without writing to GitHub:

```bash
leetcode-sync sync --dry-run
```

Sync everything:

```bash
leetcode-sync sync
```

Sync submissions since a date:

```bash
leetcode-sync sync --since 2026-01-01
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
- Re-running sync is idempotent and creates no commit when nothing changed.
- `sync --dry-run` prints planned creates, updates, and skips without writing.
- GitHub writes are all-or-nothing through a single commit.
- Secrets are redacted from error messages.

## Uninstall Or Reset

Local cleanup is manual and non-destructive:

```bash
rm -rf .venv .pytest_cache
rm -f .env
```

To remove synced files from GitHub, delete them in the target repository yourself so you can review exactly what will be removed.

## Tests

```bash
pytest
```
