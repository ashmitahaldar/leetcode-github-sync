from pathlib import Path

import pytest

from leetcode_sync.config import load_config
from leetcode_sync.errors import ConfigError


def test_load_config_valid(tmp_path: Path):
    path = tmp_path / "leetcode-sync.toml"
    path.write_text(
        """
[github]
owner = "octocat"
repo = "leetcode"
branch = "main"

[sync]
problems_root = "problems"

[leetcode]
page_size = 25
""",
        encoding="utf-8",
    )

    config = load_config(path)

    assert config.github.owner == "octocat"
    assert config.github.repo == "leetcode"
    assert config.leetcode.page_size == 25


def test_load_config_rejects_placeholder(tmp_path: Path):
    path = tmp_path / "leetcode-sync.toml"
    path.write_text(
        """
[github]
owner = "your-github-username"
repo = "your-target-repo"
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError):
        load_config(path)
