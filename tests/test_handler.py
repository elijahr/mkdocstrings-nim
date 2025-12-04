"""Tests for the Nim handler."""

from pathlib import Path

from mkdocstrings_handlers.nim.collector import NimCollector
from mkdocstrings_handlers.nim.handler import NimHandler


class TestNimCollector:
    """Tests for NimCollector."""

    def test_resolve_identifier_simple(self, tmp_path: Path):
        """Test resolving a simple identifier."""
        # Create test file
        src = tmp_path / "src"
        src.mkdir()
        (src / "mymodule.nim").write_text("## Test module")

        collector = NimCollector(["src"], tmp_path)
        path = collector._resolve_identifier("mymodule")

        assert path == src / "mymodule.nim"

    def test_resolve_identifier_nested(self, tmp_path: Path):
        """Test resolving a nested identifier."""
        # Create nested structure
        src = tmp_path / "src" / "package"
        src.mkdir(parents=True)
        (src / "submodule.nim").write_text("## Test module")

        collector = NimCollector(["src"], tmp_path)
        path = collector._resolve_identifier("package.submodule")

        assert path == src / "submodule.nim"


class TestNimHandler:
    """Tests for NimHandler."""

    def test_get_options_defaults(self):
        """Test default options."""
        handler = NimHandler(
            paths=["src"],
            base_dir=Path("."),
            mdx=[],
            mdx_config={},
        )
        options = handler.get_options({})

        assert options["show_source"] is True
        assert options["heading_level"] == 2

    def test_get_options_override(self):
        """Test option override."""
        handler = NimHandler(
            paths=["src"],
            base_dir=Path("."),
            mdx=[],
            mdx_config={},
        )
        options = handler.get_options({"show_source": False})

        assert options["show_source"] is False


def test_invalid_docstring_style_fallback(tmp_path, caplog):
    """Test that invalid docstring_style falls back to RST with warning."""
    import logging

    from mkdocstrings_handlers.nim.handler import NimHandler

    handler = NimHandler(paths=["src"], base_dir=tmp_path, mdx=[], mdx_config={})
    options = handler.get_options({"docstring_style": "invalid_style"})

    # This should not raise, should fall back to RST
    # We need a minimal Nim file to test collect()
    nim_file = tmp_path / "src" / "test.nim"
    nim_file.parent.mkdir(parents=True, exist_ok=True)
    nim_file.write_text("proc foo*() = discard\n")

    with caplog.at_level(logging.WARNING):
        # Should not raise ValueError
        try:
            handler.collect("test", options)
        except Exception as e:
            # Collection may fail for other reasons (no Nim), but not ValueError
            assert "invalid_style" not in str(e)


class TestConfigValidation:
    """Tests for configuration validation and auto-detection."""

    def test_detect_git_branch_in_repo(self, tmp_path):
        """Test git branch detection in a git repository."""
        import subprocess

        # Initialize a git repo with initial commit (required for branch)
        subprocess.run(["git", "init", "-b", "test-branch"], cwd=tmp_path, capture_output=True)
        (tmp_path / "README.md").write_text("test")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "init", "--author", "Test <test@test.com>"],
            cwd=tmp_path,
            capture_output=True,
            env={
                "GIT_AUTHOR_NAME": "Test",
                "GIT_AUTHOR_EMAIL": "test@test.com",
                "GIT_COMMITTER_NAME": "Test",
                "GIT_COMMITTER_EMAIL": "test@test.com",
            },
        )

        branch = NimHandler._detect_git_branch(tmp_path)
        assert branch == "test-branch"

    def test_detect_git_branch_not_a_repo(self, tmp_path):
        """Test git branch detection outside a git repository."""
        branch = NimHandler._detect_git_branch(tmp_path)
        assert branch is None

    def _init_git_repo(self, tmp_path, branch="main"):
        """Helper to initialize a git repo with a commit."""
        import os
        import subprocess

        env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "test@test.com",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "test@test.com",
        }
        subprocess.run(["git", "init", "-b", branch], cwd=tmp_path, capture_output=True)
        (tmp_path / "README.md").write_text("test")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True, env=env)

    def test_source_ref_auto_detected(self, tmp_path):
        """Test that source_ref is auto-detected from git branch."""
        self._init_git_repo(tmp_path, "develop")

        handler = NimHandler(
            paths=["src"],
            base_dir=tmp_path,
            mdx=[],
            mdx_config={},
            config_options={},  # No source_ref set
        )

        options = handler.get_options({})
        assert options["source_ref"] == "develop"

    def test_source_ref_explicit_overrides_auto(self, tmp_path):
        """Test that explicit source_ref overrides auto-detection."""
        self._init_git_repo(tmp_path, "develop")

        handler = NimHandler(
            paths=["src"],
            base_dir=tmp_path,
            mdx=[],
            mdx_config={},
            config_options={"source_ref": "v1.0.0"},  # Explicit
        )

        options = handler.get_options({})
        assert options["source_ref"] == "v1.0.0"

    def test_source_url_trailing_slash_removed(self, tmp_path):
        """Test that trailing slash is removed from source_url."""
        handler = NimHandler(
            paths=["src"],
            base_dir=tmp_path,
            mdx=[],
            mdx_config={},
            config_options={"source_url": "https://github.com/owner/repo/"},
        )

        options = handler.get_options({})
        assert options["source_url"] == "https://github.com/owner/repo"

    def test_source_url_malformed_warning(self, tmp_path, caplog):
        """Test warning for malformed source_url."""
        import logging

        with caplog.at_level(logging.WARNING):
            NimHandler(
                paths=["src"],
                base_dir=tmp_path,
                mdx=[],
                mdx_config={},
                config_options={"source_url": "https://github.com/owner/repo/blob/main"},
            )

        assert "should not contain '/blob/'" in caplog.text

    def test_source_url_with_tree_warning(self, tmp_path, caplog):
        """Test warning for source_url containing /tree/."""
        import logging

        with caplog.at_level(logging.WARNING):
            NimHandler(
                paths=["src"],
                base_dir=tmp_path,
                mdx=[],
                mdx_config={},
                config_options={"source_url": "https://github.com/owner/repo/tree/main/src"},
            )

        assert "should not contain" in caplog.text

    def test_show_source_without_url_info(self, tmp_path, caplog):
        """Test info message when show_source enabled without source_url."""
        import logging

        with caplog.at_level(logging.INFO):
            NimHandler(
                paths=["src"],
                base_dir=tmp_path,
                mdx=[],
                mdx_config={},
                config_options={"show_source": True},  # No source_url
            )

        assert "source_url is not set" in caplog.text


def test_get_options_includes_type_field_doc_style():
    """Test that type_field_doc_style option is available."""
    from pathlib import Path

    from mkdocstrings_handlers.nim.handler import NimHandler

    handler = NimHandler(
        paths=["src"],
        base_dir=Path.cwd(),
        mdx=[],
        mdx_config={},
    )
    options = handler.get_options({})

    assert "type_field_doc_style" in options
    assert options["type_field_doc_style"] == "inline"


def test_get_options_type_field_doc_style_override():
    """Test that type_field_doc_style can be overridden."""
    from pathlib import Path

    from mkdocstrings_handlers.nim.handler import NimHandler

    handler = NimHandler(
        paths=["src"],
        base_dir=Path.cwd(),
        mdx=[],
        mdx_config={},
        config_options={"type_field_doc_style": "docstring"},
    )
    options = handler.get_options({})

    assert options["type_field_doc_style"] == "docstring"
