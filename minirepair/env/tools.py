"""Tools: read_file, search_code, edit_file, run_tests, submit."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from minirepair.env.action_schema import Action, ToolName
from minirepair.env.guardrails import check_edit
from minirepair.env.sandbox import Sandbox


@dataclass
class Observation:
    status: str  # "success", "error", "submitted"
    content: str = ""
    error: str = ""
    tool_name: str = ""
    info: dict = field(default_factory=dict)


@dataclass
class ToolState:
    """Tracks episode-level budgets for tools."""

    edit_count: int = 0
    test_count: int = 0
    episode_edit_limit: int = 2
    episode_test_limit: int = 2


def _is_path_inside_repo(repo_path: Path, target: Path) -> bool:
    """Check that target is inside repo_path (no escape)."""
    try:
        target.resolve().relative_to(repo_path.resolve())
        return True
    except ValueError:
        return False


def read_file(sandbox: Sandbox, action: Action) -> Observation:
    """Read a file from the sandbox repo. Max 200 lines by default."""
    path = action.arguments.path
    if not path:
        return Observation(status="error", error="Missing 'path' argument", tool_name="read_file")

    if sandbox.working_path is None:
        return Observation(status="error", error="Sandbox not initialized", tool_name="read_file")

    file_path = sandbox.working_path / path
    if not _is_path_inside_repo(sandbox.working_path, file_path):
        return Observation(status="error", error="Path escapes repo boundary", tool_name="read_file")

    if not file_path.exists():
        return Observation(status="error", error=f"File not found: {path}", tool_name="read_file")

    if file_path.is_dir():
        return Observation(status="error", error=f"Path is a directory: {path}", tool_name="read_file")

    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return Observation(status="error", error=f"Cannot read binary file: {path}", tool_name="read_file")

    max_lines = action.arguments.max_lines or 200
    lines = content.split("\n")
    truncated = len(lines) > max_lines
    if truncated:
        lines = lines[:max_lines]

    result = "\n".join(lines)
    info: dict = {"path": path, "total_lines": len(content.split("\n")), "returned_lines": len(lines)}
    if truncated:
        info["truncated"] = True

    return Observation(status="success", content=result, tool_name="read_file", info=info)


def search_code(sandbox: Sandbox, action: Action) -> Observation:
    """Search for a pattern in src/ directory only."""
    query = action.arguments.query
    if not query:
        return Observation(status="error", error="Missing 'query' argument", tool_name="search_code")

    if sandbox.working_path is None:
        return Observation(status="error", error="Sandbox not initialized", tool_name="search_code")

    src_dir = sandbox.working_path / "src"
    if not src_dir.exists():
        return Observation(status="error", error="src/ directory not found", tool_name="search_code")

    matches: list[str] = []
    for py_file in src_dir.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for i, line in enumerate(content.split("\n"), 1):
            if query in line:
                rel = py_file.relative_to(sandbox.working_path)
                matches.append(f"{rel}:{i}: {line.strip()}")

    if not matches:
        return Observation(status="success", content=f"No matches for '{query}' in src/", tool_name="search_code")

    return Observation(
        status="success",
        content="\n".join(matches),
        tool_name="search_code",
        info={"match_count": len(matches), "query": query},
    )


def edit_file(
    sandbox: Sandbox,
    action: Action,
    state: ToolState,
) -> Observation:
    """Apply a search-replace edit with guardrail checks."""
    path = action.arguments.path
    old_text = action.arguments.old_text
    new_text = action.arguments.new_text

    if not path:
        return Observation(status="error", error="Missing 'path' argument", tool_name="edit_file")
    if old_text is None:
        return Observation(status="error", error="Missing 'old_text' argument", tool_name="edit_file")
    if new_text is None:
        return Observation(status="error", error="Missing 'new_text' argument", tool_name="edit_file")

    # Check edit budget
    if state.edit_count >= state.episode_edit_limit:
        return Observation(
            status="error",
            error=f"Edit budget exceeded ({state.edit_count}/{state.episode_edit_limit})",
            tool_name="edit_file",
            info={"edit_count": state.edit_count, "limit": state.episode_edit_limit},
        )

    if sandbox.working_path is None:
        return Observation(status="error", error="Sandbox not initialized", tool_name="edit_file")

    file_path = sandbox.working_path / path
    if not _is_path_inside_repo(sandbox.working_path, file_path):
        return Observation(status="error", error="Path escapes repo boundary", tool_name="edit_file")

    if not file_path.exists():
        return Observation(status="error", error=f"File not found: {path}", tool_name="edit_file")

    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return Observation(status="error", error=f"Cannot read binary file: {path}", tool_name="edit_file")

    # Count occurrences of old_text
    occurrences = content.count(old_text)

    # Run guardrails
    violations = check_edit(sandbox.working_path, action, occurrences)
    block_violations = [v for v in violations if v.severity == "block"]
    warn_violations = [v for v in violations if v.severity == "warn"]

    if block_violations:
        return Observation(
            status="error",
            error=f"Guardrail violation: {block_violations[0].message}",
            tool_name="edit_file",
            info={"violations": [{"rule": v.rule, "severity": v.severity, "message": v.message} for v in violations]},
        )

    # Apply the edit
    new_content = content.replace(old_text, new_text, 1)
    file_path.write_text(new_content, encoding="utf-8")

    state.edit_count += 1

    info: dict = {"path": path, "edit_count": state.edit_count, "limit": state.episode_edit_limit}
    if warn_violations:
        info["warnings"] = [{"rule": v.rule, "message": v.message} for v in warn_violations]

    return Observation(
        status="success",
        content=f"Edited {path} successfully",
        tool_name="edit_file",
        info=info,
    )


def run_tests(
    sandbox: Sandbox,
    action: Action,
    state: ToolState,
) -> Observation:
    """Run public tests in the sandbox."""
    test_dir = action.arguments.test_dir or "tests"

    # Check test budget
    if state.test_count >= state.episode_test_limit:
        return Observation(
            status="error",
            error=f"Test budget exceeded ({state.test_count}/{state.episode_test_limit})",
            tool_name="run_tests",
            info={"test_count": state.test_count, "limit": state.episode_test_limit},
        )

    result = sandbox.run_pytest(test_dirs=[test_dir])
    state.test_count += 1

    status = "success" if result.returncode == 0 else "error"
    return Observation(
        status=status,
        content=result.stdout,
        error=result.stderr if result.returncode != 0 else "",
        tool_name="run_tests",
        info={
            "returncode": result.returncode,
            "passed": result.passed,
            "failed": result.failed,
            "test_count": state.test_count,
            "limit": state.episode_test_limit,
            "test_dir": test_dir,
        },
    )


def submit(sandbox: Sandbox, action: Action) -> Observation:
    """Submit the current state. No reward calculation in this phase."""
    return Observation(
        status="submitted",
        content="Episode submitted",
        tool_name="submit",
    )


def execute_tool(
    sandbox: Sandbox,
    action: Action,
    state: ToolState,
) -> Observation:
    """Dispatch to the appropriate tool based on action.tool."""
    dispatch = {
        ToolName.READ_FILE: lambda: read_file(sandbox, action),
        ToolName.SEARCH_CODE: lambda: search_code(sandbox, action),
        ToolName.EDIT_FILE: lambda: edit_file(sandbox, action, state),
        ToolName.RUN_TESTS: lambda: run_tests(sandbox, action, state),
        ToolName.SUBMIT: lambda: submit(sandbox, action),
    }
    handler = dispatch.get(action.tool)
    if handler is None:
        return Observation(status="error", error=f"Unknown tool: {action.tool}")
    return handler()
