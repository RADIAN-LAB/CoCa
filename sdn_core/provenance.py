"""Record how a result was produced, so any number can be traced back.

Every result JSON carries a ``provenance`` block. Without it there is no way to
tell, months later, which code state and which parameters produced a figure —
the existing ``experiments/`` tree already contains result files whose
generating configuration can only be guessed at.
"""
from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parents[1]


def _git(*args: str, cwd: Path) -> Optional[str]:
    """Run a git command, returning None if it fails or git is unavailable."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode:
        return None
    return result.stdout.strip() or None


def git_state(repo: Optional[Path] = None) -> Dict[str, Any]:
    """Commit, branch and dirty-flag for a repository."""
    cwd = repo or ROOT
    if not (cwd / ".git").exists() and _git("rev-parse", "--git-dir", cwd=cwd) is None:
        return {"available": False}
    dirty = _git("status", "--porcelain", cwd=cwd)
    return {
        "available": True,
        "commit": _git("rev-parse", "HEAD", cwd=cwd),
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD", cwd=cwd),
        # True means uncommitted changes were present: the commit alone does not
        # identify the code that ran.
        "dirty": bool(dirty),
    }


def package_versions() -> Dict[str, str]:
    """Versions of the packages that can change numerical results."""
    versions: Dict[str, str] = {}
    for name in ("numpy", "torch", "pulp", "scipy", "pandas", "xgboost"):
        try:
            module = __import__(name)
        except ImportError:
            versions[name] = "not installed"
            continue
        versions[name] = getattr(module, "__version__", "unknown")
    return versions


def sumo_version() -> Optional[str]:
    """First line of ``sumo --version``, or None if SUMO is unavailable."""
    try:
        result = subprocess.run(
            ["sumo", "--version"], capture_output=True, text=True, timeout=15
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode:
        return None
    for line in result.stdout.splitlines():
        if line.strip():
            return line.strip()
    return None


def provenance(
    params: Optional[Dict[str, Any]] = None,
    repos: Optional[Dict[str, Path]] = None,
    include_sumo: bool = False,
) -> Dict[str, Any]:
    """Assemble a provenance block for embedding in a result JSON.

    Args:
        params: The full parameter set of the run (seeds, modes, capacities...).
            Record everything that could change the numbers.
        repos: Mapping of label -> repository path. Defaults to the CoCa root.
        include_sumo: Query the SUMO version too. Off by default because it
            spawns a subprocess and only matters for trace generation.
    """
    block: Dict[str, Any] = {
        "params": dict(params or {}),
        "git": {
            label: git_state(path)
            for label, path in (repos or {"coca": ROOT}).items()
        },
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": package_versions(),
    }
    if include_sumo:
        block["sumo"] = sumo_version()
    return block


__all__ = [
    "git_state",
    "package_versions",
    "provenance",
    "sumo_version",
]
