"""Clamper DNA Analyzer — Deep project DNA extraction via MCP.

This is what CLAUDE.md CAN'T do — it's dynamic, analyzing real git history,
dependency graphs, test coverage patterns, and architecture in real-time.
"""

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("clamper-dna")


def _run_git(cmd: list[str], cwd: str, timeout: int = 30) -> str:
    """Run a git command safely."""
    try:
        result = subprocess.run(
            ["git"] + cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return ""


def _detect_stack(project_path: str) -> dict:
    """Detect project technology stack from manifest files."""
    stack = {"languages": [], "frameworks": [], "build": [], "test": []}
    p = Path(project_path)

    manifest_map = {
        "package.json": ("javascript/typescript", "node"),
        "pyproject.toml": ("python", "python"),
        "Cargo.toml": ("rust", "cargo"),
        "go.mod": ("go", "go"),
        "Gemfile": ("ruby", "bundler"),
        "pom.xml": ("java", "maven"),
        "build.gradle": ("java/kotlin", "gradle"),
        "Makefile": (None, "make"),
        "Dockerfile": (None, "docker"),
    }

    for manifest, (lang, build) in manifest_map.items():
        if (p / manifest).exists():
            if lang:
                stack["languages"].append(lang)
            stack["build"].append(build)

    # Detect frameworks from package.json
    pkg_json = p / "package.json"
    if pkg_json.exists():
        try:
            with open(pkg_json) as f:
                pkg = json.load(f)
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            framework_map = {
                "react": "React", "vue": "Vue", "svelte": "Svelte",
                "next": "Next.js", "nuxt": "Nuxt", "express": "Express",
                "fastify": "Fastify", "hono": "Hono", "tailwindcss": "Tailwind",
                "@angular/core": "Angular", "htmx.org": "HTMX",
            }
            for dep, name in framework_map.items():
                if dep in deps:
                    stack["frameworks"].append(name)

            test_map = {"jest": "Jest", "vitest": "Vitest", "mocha": "Mocha", "playwright": "Playwright"}
            for dep, name in test_map.items():
                if dep in deps:
                    stack["test"].append(name)
        except (json.JSONDecodeError, OSError):
            pass

    # Detect Python frameworks from pyproject.toml
    pyproject = p / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text()
            py_frameworks = {
                "django": "Django", "flask": "Flask", "fastapi": "FastAPI",
                "fastmcp": "FastMCP", "anthropic": "Anthropic SDK",
            }
            for dep, name in py_frameworks.items():
                if dep in content.lower():
                    stack["frameworks"].append(name)
            if "pytest" in content:
                stack["test"].append("pytest")
        except OSError:
            pass

    return stack


@mcp.tool
async def extract_project_dna(project_path: str) -> dict:
    """Analyze a project for deep DNA: architecture patterns, hot files,
    coupling graphs, test coverage gaps, and commit velocity by module.

    This goes far beyond static CLAUDE.md — it's live analysis of the
    project's actual state from git history and file structure.
    """
    if not os.path.isdir(project_path):
        return {"error": f"Directory not found: {project_path}"}

    dna = {
        "project": os.path.basename(project_path),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stack": _detect_stack(project_path),
        "hot_files": [],
        "fragile_zones": [],
        "coupling_groups": [],
        "test_coverage": {},
        "dependency_hotspots": [],
        "commit_velocity": {},
    }

    # Hot files: most changed in last 100 commits
    log_output = _run_git(
        ["log", "--oneline", "-100", "--name-only", "--pretty=format:"],
        project_path
    )
    if log_output:
        file_counts = {}
        for line in log_output.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("'"):
                file_counts[line] = file_counts.get(line, 0) + 1

        hot_files = sorted(file_counts.items(), key=lambda x: -x[1])[:20]
        dna["hot_files"] = [{"file": f, "changes": c} for f, c in hot_files]

        # Commit velocity by directory
        dir_counts = {}
        for f, c in file_counts.items():
            if "/" in f:
                d = f.split("/")[0]
                dir_counts[d] = dir_counts.get(d, 0) + c
        dna["commit_velocity"] = dict(sorted(dir_counts.items(), key=lambda x: -x[1])[:10])

    # Coupling: files that change together
    commits_output = _run_git(
        ["log", "--oneline", "-100", "--name-only", "--pretty=format:---"],
        project_path
    )
    if commits_output:
        from collections import Counter
        commits = []
        current = []
        for line in commits_output.split("\n"):
            line = line.strip()
            if line == "---":
                if current:
                    commits.append(current)
                current = []
            elif line:
                current.append(line)
        if current:
            commits.append(current)

        pairs = Counter()
        for files in commits:
            for i, a in enumerate(files):
                for b in files[i + 1:]:
                    pair = tuple(sorted([a, b]))
                    pairs[pair] += 1

        dna["coupling_groups"] = [
            {"files": list(pair), "co_changes": count}
            for pair, count in pairs.most_common(15)
            if count >= 3
        ]

    # Fragile zones: high churn + no tests
    for hot in dna["hot_files"]:
        if hot["changes"] < 5:
            continue
        filepath = hot["file"]
        basename = os.path.splitext(os.path.basename(filepath))[0]

        # Check for test file
        test_patterns = [
            f"test_{basename}", f"{basename}_test", f"{basename}.test",
            f"{basename}.spec", f"test_{basename}"
        ]
        has_test = False
        for pattern in test_patterns:
            result = subprocess.run(
                ["find", project_path, "-name", f"{pattern}.*", "-type", "f"],
                capture_output=True, text=True, timeout=10
            )
            if result.stdout.strip():
                has_test = True
                break

        if not has_test:
            dna["fragile_zones"].append({
                "file": filepath,
                "changes": hot["changes"],
                "reason": "high churn, no test file found"
            })

    # Test coverage map
    test_dirs = []
    for dirpath, dirnames, filenames in os.walk(project_path):
        # Skip hidden dirs and node_modules
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "node_modules"]
        rel = os.path.relpath(dirpath, project_path)
        test_files = [f for f in filenames if re.match(r"(test_|.*_test\.|.*\.test\.|.*\.spec\.)", f)]
        source_files = [f for f in filenames if f.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".rs", ".go"))
                        and not re.match(r"(test_|.*_test\.|.*\.test\.|.*\.spec\.)", f)]
        if test_files or source_files:
            dna["test_coverage"][rel] = {
                "test_files": len(test_files),
                "source_files": len(source_files),
                "ratio": f"{len(test_files)}:{len(source_files)}"
            }

    # Dependency hotspots (most imported files)
    import_counts = {}
    for dirpath, dirnames, filenames in os.walk(project_path):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "node_modules" and d != "__pycache__"]
        for fname in filenames:
            if fname.endswith((".py", ".ts", ".tsx", ".js", ".jsx")):
                fpath = os.path.join(dirpath, fname)
                try:
                    with open(fpath, "r", errors="replace") as f:
                        content = f.read(10000)  # First 10KB
                    imports = re.findall(r'(?:from|import)\s+["\']?([\w./]+)', content)
                    for imp in imports:
                        import_counts[imp] = import_counts.get(imp, 0) + 1
                except OSError:
                    continue

    dna["dependency_hotspots"] = [
        {"module": mod, "imported_by": count}
        for mod, count in sorted(import_counts.items(), key=lambda x: -x[1])[:10]
        if count >= 3
    ]

    return dna


@mcp.tool
async def get_fragile_zones(project_path: str) -> list:
    """Identify code zones with high churn and low test coverage.
    These are the files most likely to break silently."""
    dna = await extract_project_dna(project_path)
    return dna.get("fragile_zones", [])


@mcp.tool
async def get_coupling_map(project_path: str) -> list:
    """Get files that frequently change together, revealing hidden dependencies."""
    dna = await extract_project_dna(project_path)
    return dna.get("coupling_groups", [])


@mcp.tool
async def get_hot_files(project_path: str, min_changes: int = 3) -> list:
    """Get the most frequently modified files in recent git history."""
    dna = await extract_project_dna(project_path)
    return [f for f in dna.get("hot_files", []) if f["changes"] >= min_changes]
