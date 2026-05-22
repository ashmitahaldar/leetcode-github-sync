README_TEMPLATE = """# LeetCode GitHub Sync

A lightweight Python CLI that syncs accepted LeetCode submissions into an existing GitHub repository.

## Setup

1. Edit `leetcode-sync.toml` with your GitHub owner, repo, and branch.
2. Copy `.env.example` to `.env`.
3. Fill in `LEETCODE_SESSION`, optional `CSRFTOKEN`, and `GITHUB_TOKEN`.
4. Run `leetcode-sync status`.
5. Preview with `leetcode-sync sync --dry-run`.
6. Sync with `leetcode-sync sync`.

Generated solution files and `metadata.json` may be updated by the tool. `notes.md` is created once and never overwritten.
"""

CONFIG_TEMPLATE = """[github]
owner = "your-github-username"
repo = "your-target-repo"
branch = "main"

[sync]
problems_root = "problems"
create_notes = true
request_delay_seconds = 0.35
max_retries = 3

[leetcode]
page_size = 50
"""

ENV_EXAMPLE_TEMPLATE = """# Copy this file to .env and fill in real values.
# Never commit .env.

LEETCODE_SESSION=
CSRFTOKEN=
GITHUB_TOKEN=
"""

GITIGNORE_ENTRIES = [".env", ".venv/", "__pycache__/", "*.py[cod]", ".pytest_cache/"]
