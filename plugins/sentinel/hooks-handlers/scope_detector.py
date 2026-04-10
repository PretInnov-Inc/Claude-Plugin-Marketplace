#!/usr/bin/env python3
"""Sentinel Scope Detector — git-aware OR file-tracking scope resolution.

The key innovation: every other review plugin breaks without git.
Sentinel uses a dual-mode approach:
  1. Git mode: uses git diff/status when available
  2. File-tracking mode: uses the edit log from PostToolUse hooks

Both modes produce the same output format so all downstream agents
work identically regardless of the source.

Usage:
  python3 scope_detector.py [--session-id ID] [--explicit-files file1 file2 ...]

Output (JSON to stdout):
  {
    "mode": "git" | "file-tracking",
    "files": [{"path": "...", "status": "modified|added|deleted", "risk_signals": [...]}],
    "summary": "..."
  }
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def is_git_repo(cwd=None):
    """Check if current directory is inside a git repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, timeout=5,
            cwd=cwd
        )
        return result.returncode == 0 and result.stdout.strip() == "true"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_git_root(cwd=None):
    """Get the root directory of the git repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5,
            cwd=cwd
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def git_changed_files(cwd=None):
    """Get changed files from git diff (staged + unstaged + untracked)."""
    files = []

    # Unstaged changes
    try:
        result = subprocess.run(
            ["git", "diff", "--name-status"],
            capture_output=True, text=True, timeout=10,
            cwd=cwd
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("\t", 1)
                if len(parts) == 2:
                    status_map = {"M": "modified", "A": "added", "D": "deleted"}
                    status = status_map.get(parts[0], "modified")
                    files.append({"path": parts[1], "status": status, "source": "unstaged"})
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Staged changes
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-status"],
            capture_output=True, text=True, timeout=10,
            cwd=cwd
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("\t", 1)
                if len(parts) == 2:
                    status_map = {"M": "modified", "A": "added", "D": "deleted"}
                    status = status_map.get(parts[0], "modified")
                    existing = [f for f in files if f["path"] == parts[1]]
                    if not existing:
                        files.append({"path": parts[1], "status": status, "source": "staged"})
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Untracked files
    try:
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True, text=True, timeout=10,
            cwd=cwd
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if line and not any(f["path"] == line for f in files):
                    files.append({"path": line, "status": "added", "source": "untracked"})
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return files


def file_tracking_changed_files(data_dir, session_id=None):
    """Get changed files from the edit log (non-git mode).

    Reads edit-log.jsonl entries from the current session to determine
    which files were modified, effectively replacing git diff.
    """
    log_path = os.path.join(data_dir, "edit-log.jsonl")
    if not os.path.exists(log_path):
        return []

    file_map = {}
    try:
        with open(log_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if entry.get("event") != "edit_tracked":
                    continue

                # Filter by session if provided
                if session_id and entry.get("session_id") != session_id:
                    continue

                file_path = entry.get("file_path", "")
                if not file_path:
                    continue

                tool = entry.get("tool", "")
                if file_path not in file_map:
                    file_map[file_path] = {
                        "path": file_path,
                        "status": "added" if tool == "Write" else "modified",
                        "source": "edit-log",
                        "edit_count": 0,
                        "risk_signals": []
                    }

                file_map[file_path]["edit_count"] += 1
                for signal in entry.get("risk_signals", []):
                    if signal not in file_map[file_path]["risk_signals"]:
                        file_map[file_path]["risk_signals"].append(signal)

    except (IOError, OSError):
        pass

    return list(file_map.values())


def classify_risk(file_path):
    """Classify risk signals for a file path."""
    signals = []
    path_lower = file_path.lower()
    basename = os.path.basename(path_lower)

    # Test files
    if any(p in path_lower for p in ["test_", "_test.", ".test.", "spec.", "tests/", "__tests__"]):
        signals.append("test-file")

    # Config/build files
    config_patterns = [
        "package.json", "pyproject.toml", "cargo.toml", "go.mod", "go.sum",
        "makefile", "dockerfile", "docker-compose", ".env",
        "settings.py", "tsconfig", "webpack", "vite.config", "rollup.config",
        "babel.config", ".eslintrc", ".prettierrc", "jest.config",
        "requirements.txt", "setup.py", "setup.cfg", "pipfile",
        "gemfile", "build.gradle", "pom.xml", "cmakelists.txt"
    ]
    if any(p in path_lower for p in config_patterns):
        signals.append("config-file")

    # Security-sensitive files
    security_patterns = [
        "auth", "login", "permission", "token", "session", "crypto",
        "secret", "password", "credential", "oauth", "jwt", "csrf",
        "sanitize", "escape", "encrypt", "decrypt", "certificate", "ssl", "tls"
    ]
    if any(p in path_lower for p in security_patterns):
        signals.append("security-sensitive")

    # Database/migration files
    if any(p in path_lower for p in ["migration", "schema", "seed", "fixture", "sql"]):
        signals.append("database")

    # API/route files
    if any(p in path_lower for p in ["route", "endpoint", "controller", "handler", "middleware", "api/"]):
        signals.append("api-layer")

    # CI/CD files
    if any(p in path_lower for p in [".github/workflows", ".gitlab-ci", "jenkinsfile", ".circleci", ".travis"]):
        signals.append("ci-cd")

    return signals


def detect_scope(data_dir, session_id=None, explicit_files=None, cwd=None):
    """Main scope detection: git-first with file-tracking fallback."""

    # If explicit files provided, use those directly
    if explicit_files:
        files = []
        for fp in explicit_files:
            files.append({
                "path": fp,
                "status": "explicit",
                "source": "user-specified",
                "risk_signals": classify_risk(fp)
            })
        return {
            "mode": "explicit",
            "files": files,
            "summary": f"{len(files)} file(s) specified by user"
        }

    # Try git first
    if is_git_repo(cwd):
        files = git_changed_files(cwd)
        for f in files:
            f["risk_signals"] = classify_risk(f["path"])

        # If git found changes, use git mode
        if files:
            return {
                "mode": "git",
                "files": files,
                "summary": f"{len(files)} file(s) changed (git diff)"
            }

        # Git repo but no changes — check edit log for session-only edits
        ft_files = file_tracking_changed_files(data_dir, session_id)
        if ft_files:
            return {
                "mode": "git+file-tracking",
                "files": ft_files,
                "summary": f"No git diff, but {len(ft_files)} file(s) edited this session"
            }

        return {
            "mode": "git",
            "files": [],
            "summary": "No changes detected (git clean, no session edits)"
        }

    # No git — use file tracking
    ft_files = file_tracking_changed_files(data_dir, session_id)
    for f in ft_files:
        if "risk_signals" not in f or not f["risk_signals"]:
            f["risk_signals"] = classify_risk(f["path"])

    if ft_files:
        return {
            "mode": "file-tracking",
            "files": ft_files,
            "summary": f"Non-git project: {len(ft_files)} file(s) edited this session"
        }

    return {
        "mode": "file-tracking",
        "files": [],
        "summary": "Non-git project: no edits tracked yet this session"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Sentinel scope detector")
    parser.add_argument("--session-id", default=None)
    parser.add_argument("--explicit-files", nargs="*", default=None)
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--cwd", default=None)
    args = parser.parse_args()

    data_dir = args.data_dir
    if not data_dir:
        plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
        if plugin_root:
            data_dir = os.path.join(plugin_root, "data")
        else:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

    result = detect_scope(
        data_dir=data_dir,
        session_id=args.session_id,
        explicit_files=args.explicit_files,
        cwd=args.cwd
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
