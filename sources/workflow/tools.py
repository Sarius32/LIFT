import base64
import shutil
from pathlib import Path
from typing import Any, Optional, Dict, List

from env import PROJECT_PATH
from project_utils import tool_metadata
from requirements import get_structured_reqs, get_requirements_only


def safe_path(rel: str) -> Optional[Path]:
    """
    Resolve a user path inside ROOT, preventing escape outside the repo.
    Returns None if the path is outside ROOT.
    """
    p = (PROJECT_PATH / rel).resolve()
    if p != PROJECT_PATH and PROJECT_PATH not in p.parents:
        return None
    return p


@tool_metadata(
    description="Recursively list files and directories under a path (relative to repo root), filtered by a glob. "
                "Can optionally include hidden entries.",
    properties={
        "path": {
            "type": "string",
            "description": "Starting directory relative to repo root.",
            "default": ".",
        },
        "glob": {
            "type": "string",
            "description": "Glob pattern to filter results.",
            "default": "*",
        },
        "include_hidden": {
            "type": "boolean",
            "description": "Include hidden files/folders (names starting with '.').",
            "default": False,
        },
    }
)
def tool_list_dir(path: str = ".", glob: str = "*", include_hidden: bool = False) -> Dict[str, Any]:
    """
    Recursively list all files and directories under the given path, filtered by glob.

    Args:
        path (str): Starting directory relative to the repo root. Defaults to "." (root).
        glob (str): Glob pattern to filter results. Defaults to "*" (everything).
        include_hidden (bool): Whether to include hidden files/folders (names starting with '.').
    """
    p = safe_path(path)
    if p is None:
        return {"error": f"Path escapes ROOT: {path}"}
    if not p.exists():
        return {"error": f"Path not found: {path}"}

    entries = []
    for child in p.rglob(glob):
        rel_path = child.relative_to(PROJECT_PATH)
        # always skip caches
        if any("cache" in part for part in rel_path.parts):
            continue
        # Skip hidden entries if not allowed
        if not include_hidden:
            if not include_hidden and any(part.startswith(".") for part in rel_path.parts):
                continue
        rel = rel_path.as_posix()
        if child.is_dir():
            entries.append({"path": rel + "/", "is_directory": True})
        else:
            entries.append({"path": rel, "is_file": True, "bytes_size": len(child.read_bytes())})

    return {"entries": sorted(entries, key=lambda e: e["path"])}


def _read_file_common(rel: str, offset: int, max_bytes: int) -> Dict[str, Any]:
    """
    Internal helper to read a single file safely.

    Always returns a dict with at least:
      - "path": str
      - On success:
          * "text": UTF-8 decoded string (if decodable) OR
          * "base64_data": Base64-encoded string of file bytes (with "encoding": "base64")
        plus:
          * "truncated": bool — True if file was cut to `max_bytes`
      - On error:
          * "error": str — reason the read failed (e.g., "not_found", "is_directory", etc.)
    """
    p = safe_path(rel)
    if p is None:
        return {"path": rel, "error": "escapes_root"}
    if not p.exists():
        return {"path": rel, "error": "not_found"}
    if p.is_dir():
        return {"path": rel, "error": "is_directory"}

    try:
        raw = p.read_bytes()
    except Exception as e:
        return {"path": rel, "error": f"read_failed: {e}"}

    if offset > len(raw):
        return {"path": rel, "error": "offset_after_EOF"}

    truncated = False
    if len(raw) > offset + max_bytes:
        raw = raw[offset:offset + max_bytes]
        truncated = True

    try:
        text = raw.decode("utf-8")
        return {"path": rel, "text": text, "truncated": truncated}
    except UnicodeDecodeError:
        b64 = base64.b64encode(raw).decode("ascii")
        return {
            "path": rel,
            "base64_data": b64,
            "encoding": "base64",
            "truncated": truncated
        }


@tool_metadata(
    description="Read up to `max_bytes` starting from `offset` from a single file under the repo root. "
                "Hidden file allowed. Returns UTF-8 text if possible, else Base64-encoded bytes.",
    properties={
        "path": {
            "type": "string",
            "description": "File path relative to repo root.",
        },
        "offset": {
            "type": "integer",
            "description": "Byte offset to start reading from.",
            "default": 0,
        },
        "max_bytes": {
            "type": "integer",
            "description": "Maximum number of bytes to read.",
            "default": 200_000,
            "minimum": 1,
        },
    },
    required=["path"]
)
def tool_read_file(path: str, offset: int = 0, max_bytes: int = 200_000) -> Dict[str, Any]:
    """
    Read up to `max_bytes` starting from the offset from a single file under the repo root.

    Returns:
      - UTF-8 text if possible.
      - Otherwise, Base64-encoded bytes.
      - Always includes "path" and "truncated" fields.
      - On error, returns only "path" and "error".
    """
    return _read_file_common(path, offset, max_bytes)


def tool_read_many(paths: List[str], offset: int = 0, max_bytes_per_file: int = 200_000) -> Dict[str, Any]:
    """
    Read multiple explicitly listed files under the repo root.

    Rules:
      - Hidden files are allowed.
      - Maximum number of files: 10 (exceeding this returns an error, no files read).
      - Maximum bytes per file is enforced by `max_bytes_per_file`.

    Returns:
      {
        "entries": [
          # One dict per file in the same format as `tool_read_file`
        ]
      }
      On error for a specific file, the file's entry will contain "path" and "error".
      If the file count limit is exceeded, returns:
        { "error": "too_many_files", "max_allowed": MAX_FILES, "requested": <count> }
    """
    MAX_FILES = 10

    if not paths:
        return {"error": "no_files_provided"}

    if len(paths) > MAX_FILES:
        return {"error": f"too_many_files", "max_allowed": MAX_FILES, "requested": len(paths)}

    entries: List[Dict[str, Any]] = []

    for rel in paths:
        entries.append(_read_file_common(rel, offset, max_bytes_per_file))

    return {"entries": sorted(entries, key=lambda e: e["path"])}


@tool_metadata(
    description="Create or overwrite a UTF-8 text file under the repo root.",
    properties={
        "path": {
            "type": "string",
            "description": "Target file path relative to repo root.",
        },
        "content": {
            "type": "string",
            "description": "UTF-8 text content to write.",
        },
        "overwrite": {
            "type": "boolean",
            "description": "If false and file exists, return an error.",
            "default": True,
        },
    },
    required=["path", "content"]
)
def tool_write_file(path: str, content: str, overwrite: bool = True) -> Dict[str, Any]:
    """
    Create or overwrite a text file (UTF-8) under the repo root.

    Args:
        path (str): Path relative to the repo root.
        content (str): File content to write.
        overwrite (bool): Whether to overwrite if the file exists.
    """
    p = safe_path(path)
    if p is None:
        return {"error": f"Path escapes ROOT: {path}"}

    try:
        p.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return {"error": f"Failed to create parent directories: {e}"}

    if p.exists() and not overwrite:
        return {"error": f"File already exists: {path}"}

    try:
        p.write_text(content, encoding="utf-8")
    except Exception as e:
        return {"error": f"Failed to write file: {e}"}

    return {"ok": True}


@tool_metadata(
    description="Delete a file or directory (recursively) under the repo root. "
                "Idempotent for missing paths; refuses to delete the repo root.",
    properties={
        "path": {
            "type": "string",
            "description": "Path relative to repo root to delete.",
        },
    },
    required=["path"]
)
def tool_delete_path(path: str) -> Dict[str, Any]:
    """
    Delete a file or directory under the repo root.
    Idempotent: returns {"ok": True} even if the path doesn't exist.
    """
    p = safe_path(path)
    if p is None:
        return {"error": f"Path escapes ROOT: {path}"}

    # Don't allow deleting the entire repo root
    if p == PROJECT_PATH:
        return {"error": "refuse_delete_root"}

    if not p.exists():
        return {"ok": True}

    try:
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
    except Exception as e:
        return {"error": f"Failed to delete path: {e}"}

    return {"ok": True}


@tool_metadata(
    description="Replace exactly one occurrence of `find` with `replace` in a UTF-8 text file. "
                "Fails if not found or not unique, or if find==replace.",
    properties={
        "path": {
            "type": "string",
            "description": "File path relative to repo root.",
        },
        "find": {
            "type": "string",
            "description": "Substring to locate (must occur exactly once).",
        },
        "replace": {
            "type": "string",
            "description": "Replacement substring (must differ from `find`).",
        },
    },
    required=["path", "find", "replace"])
def tool_replace_in_file(path: str, find: str, replace: str) -> Dict[str, Any]:
    """
    Replace exactly one occurrence of `find` with `replace` in a UTF-8 text file.

    Rules:
    - `find` must occur exactly once in the file, otherwise return an error.
    - `find` and `replace` must not be identical.
    """
    if find == replace:
        return {"error": "find_equals_replace"}

    p = safe_path(path)
    if p is None:
        return {"error": f"Path escapes ROOT: {path}"}
    if not p.exists():
        return {"error": f"Path not found: {path}"}
    if p.is_dir():
        return {"error": f"Path is a directory: {path}"}

    try:
        text = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return {"error": "not_utf8_text"}
    except Exception as e:
        return {"error": f"Failed to read file: {e}"}

    occurrences = text.count(find)
    if occurrences == 0:
        return {"error": "find_not_found", "found": 0}
    if occurrences > 1:
        return {"error": "find_not_unique", "found": occurrences}

    new_text = text.replace(find, replace, 1)
    if new_text == text:
        # Defensive guard; shouldn't happen given checks above.
        return {"error": "no_change_made"}

    try:
        p.write_text(new_text, encoding="utf-8")
    except Exception as e:
        return {"error": f"Failed to write file: {e}"}

    return {"ok": True}


@tool_metadata(
    description="Get all requirements (incl. id, title, description and acceptance) (structured).",
    properties={}
)
def tool_get_all_requirements() -> dict:
    """ Returns the ordered dict of all requirements (structured by scopes). """
    return get_structured_reqs().to_dict()


@tool_metadata(
    description="Get the ids of all available requirements.",
    properties={}
)
def tool_get_all_requirement_ids():
    """ Returns all requirement ids. """
    return [req.id for req in get_requirements_only()]


@tool_metadata(
    description="Get the details of a requirement based on its identifier.",
    properties={"identifier": {"type": "string", "description": "Requirement identifier (id)."}},
    required=["identifier"]
)
def tool_get_requirement_data(identifier: str):
    """ Returns the requirement details based on its identifier (if available). """
    req = get_structured_reqs().find_requirement(identifier)
    if req is None:
        return {"error": "identifier_unknown"}

    return req.to_dict()


@tool_metadata(
    description="Calling this function indicates the intent to end the conversation after completing all tasks. "
                "Fails if a required output is missing or the final_text is not a valid value.",
    properties={"final_text": {"type": "string", "description": "The final text of the conversation."}},
    required=["final_text"]
)
def tool_end_conversation(final_text: str):
    return final_text


available_tools = [tool_list_dir, tool_read_file, tool_write_file, tool_delete_path, tool_replace_in_file,
                   tool_get_all_requirements, tool_get_all_requirement_ids, tool_get_requirement_data,
                   tool_end_conversation]


def get_available_tools():
    impls, specs = dict(), list()
    for tool in available_tools:
        impls[tool.name] = tool

        spec = dict(type="function", name=tool.name, description=tool.description,
                    parameters=dict(type="object", properties=tool.properties))

        if tool.required:
            spec["parameters"]["required"] = tool.required

        specs.append(spec)

    return impls, specs


# ---- Tool registry ----
TOOLS_IMPL, TOOLS_SPEC = get_available_tools()
