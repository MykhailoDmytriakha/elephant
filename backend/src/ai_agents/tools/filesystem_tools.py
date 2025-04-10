# src/ai_agents/filesystem_tools.py
import os
import shutil
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import difflib
from datetime import datetime, timezone
from src.core.config import settings
from src.exceptions import ValidationException
import asyncio # Add asyncio import

try:
    from agents import function_tool, FunctionTool, RunContextWrapper # type: ignore
    AGENTS_SDK_AVAILABLE = True
except ImportError:
    logging.warning("OpenAI Agents SDK not installed. Filesystem tools might not be directly callable by agents.")
    AGENTS_SDK_AVAILABLE = False

logger = logging.getLogger(__name__)

# --- Security Validation ---
def _validate_path(requested_path_str: str, check_existence: bool = True, check_is_dir: Optional[bool] = None, allow_create: bool = False) -> Path:
    """
    Validates if a requested path is within the allowed base directory and exists (optionally).
    Resolves the path and performs security checks.
    """
    if not settings.ALLOWED_BASE_DIR_RESOLVED:
         raise ValidationException("Filesystem tools are disabled: Allowed base directory not configured.")

    expanded_path = Path(os.path.expanduser(requested_path_str))
    absolute_path = settings.ALLOWED_BASE_DIR_RESOLVED / expanded_path

    try:
         resolved_path = absolute_path.resolve(strict=False)
         if not resolved_path.exists() and allow_create:
             parent_resolved = absolute_path.parent.resolve(strict=True)
             if not parent_resolved.is_relative_to(settings.ALLOWED_BASE_DIR_RESOLVED):
                 raise ValidationException("Access denied - parent directory outside allowed scope.")
             resolved_path = absolute_path # Use non-resolved for potential creation
         elif check_existence or check_is_dir is not None:
             resolved_path = absolute_path.resolve(strict=True)

    except FileNotFoundError:
         if check_existence:
             raise
         elif allow_create:
             parent_resolved = absolute_path.parent.resolve(strict=True)
             if not parent_resolved.is_relative_to(settings.ALLOWED_BASE_DIR_RESOLVED):
                  raise ValidationException("Access denied - parent directory for creation outside allowed scope.")
             resolved_path = absolute_path
         else:
             raise
    except Exception as e:
        logger.error(f"Path resolution error for '{requested_path_str}': {e}", exc_info=True)
        raise ValidationException(f"Invalid path: {requested_path_str}")

    if not resolved_path.is_relative_to(settings.ALLOWED_BASE_DIR_RESOLVED):
         logger.warning(f"Path traversal attempt detected or path outside allowed scope: '{requested_path_str}' resolved to '{resolved_path}' which is outside '{settings.ALLOWED_BASE_DIR_RESOLVED}'")
         raise ValidationException("Access denied - path outside allowed scope.")

    if check_existence and not allow_create and not resolved_path.exists():
        raise FileNotFoundError(f"Path does not exist: {requested_path_str}")

    if check_is_dir is True and resolved_path.exists() and not resolved_path.is_dir(): # Check exists first
         raise NotADirectoryError(f"Path is not a directory: {requested_path_str}")
    if check_is_dir is False and resolved_path.exists() and not resolved_path.is_file(): # Check exists first
         raise IsADirectoryError(f"Path is not a file: {requested_path_str}")

    return resolved_path

# --- Tool Implementations ---

def _format_error(tool_name: str, path: Optional[str], message: str) -> str:
    """Formats consistent error messages for tools."""
    prefix = f"Error in {tool_name}"
    if path:
        prefix += f" for '{path}'"
    return f"{prefix}: {message}"

if AGENTS_SDK_AVAILABLE:
    @function_tool
    def list_allowed_directory() -> str:
        """
        Returns the base directory path that the filesystem tools are restricted to operate within.
        """
        logger.info("Tool executed: list_allowed_directory")
        try:
            if not settings.ALLOWED_BASE_DIR_RESOLVED:
                raise ValidationException("Filesystem tools are disabled (base directory not configured).")
            return f"Operations are restricted to the directory: {settings.ALLOWED_BASE_DIR_RESOLVED}"
        except ValidationException as e:
            logger.error(f"Error in list_allowed_directory: {e}")
            return _format_error("list_allowed_directory", None, str(e))
        except Exception as e:
            logger.exception("Unexpected error in list_allowed_directory")
            return _format_error("list_allowed_directory", None, f"Unexpected error: {e}")

    @function_tool
    def read_file(path: str) -> str:
        """
        Reads the content of a text file within the allowed directory.

        Args:
            path: The relative path to the file from the allowed base directory.

        Returns:
            The content of the file as a string, or an error message starting with 'Error:'.
        """
        logger.info(f"Tool executed: read_file (Path: {path})")
        try:
            valid_path = _validate_path(path, check_existence=True, check_is_dir=False)
            content = valid_path.read_text(encoding='utf-8')
            logger.info(f"Successfully read file: {valid_path}")
            return f"Content of '{path}':\n```\n{content}\n```"
        except (ValidationException, FileNotFoundError, IsADirectoryError, PermissionError, UnicodeDecodeError) as e:
            logger.error(f"Error reading file '{path}': {e}")
            return _format_error("read_file", path, str(e))
        except Exception as e:
            logger.exception(f"Unexpected error reading file '{path}'")
            return _format_error("read_file", path, f"Unexpected error: {e}")

    @function_tool
    def read_multiple_files(paths: List[str]) -> str:
        """
        Reads the contents of multiple text files within the allowed directory.

        Args:
            paths: A list of relative paths to the files from the allowed base directory.

        Returns:
            A string containing the contents of successfully read files,
            separated by '---', including error messages for files that could not be read.
        """
        logger.info(f"Tool executed: read_multiple_files (Paths: {paths})")
        results = []
        if not paths:
            return "Error: No file paths provided to read."

        for p in paths:
            try:
                valid_path = _validate_path(p, check_existence=True, check_is_dir=False)
                content = valid_path.read_text(encoding='utf-8')
                logger.info(f"Successfully read file: {valid_path}")
                results.append(f"--- Content of '{p}': ---\n```\n{content}\n```")
            except (ValidationException, FileNotFoundError, IsADirectoryError, PermissionError, UnicodeDecodeError) as e:
                logger.error(f"Error reading file '{p}': {e}")
                results.append(f"--- Error reading file '{p}': {e} ---")
            except Exception as e:
                logger.exception(f"Unexpected error reading file '{p}'")
                results.append(f"--- Error reading file '{p}': Unexpected error: {e} ---")
        return "\n".join(results)

    @function_tool
    def write_file(path: str, content: str) -> str:
        """
        Writes or overwrites a text file within the allowed directory.
        Parent directories must exist (use 'create_directory' first if needed).

        Args:
            path: The relative path to the file from the allowed base directory.
            content: The string content to write to the file.

        Returns:
            A confirmation message or an error message starting with 'Error:'.
        """
        logger.info(f"Tool executed: write_file (Path: {path})")
        try:
            valid_path = _validate_path(path, check_existence=False, allow_create=True, check_is_dir=False)

            parent_dir = valid_path.parent
            if not parent_dir.exists():
                if settings.ALLOWED_BASE_DIR_RESOLVED:
                    parent_rel_path = parent_dir.relative_to(settings.ALLOWED_BASE_DIR_RESOLVED)
                    raise FileNotFoundError(f"Parent directory '{parent_rel_path}' does not exist. Use create_directory first.")
                else:
                    raise FileNotFoundError(f"Parent directory '{parent_dir}' does not exist and base directory is not configured.")
            if not parent_dir.is_dir():
                 if settings.ALLOWED_BASE_DIR_RESOLVED:
                     parent_rel_path = parent_dir.relative_to(settings.ALLOWED_BASE_DIR_RESOLVED)
                     raise NotADirectoryError(f"Parent path '{parent_rel_path}' is not a directory.")
                 else:
                     raise NotADirectoryError(f"Parent path '{parent_dir}' is not a directory and base directory is not configured.")

            valid_path.write_text(content, encoding='utf-8')
            logger.info(f"Successfully wrote to file: {valid_path}")
            return f"Successfully wrote content to '{path}'."
        except (ValidationException, FileNotFoundError, NotADirectoryError, IsADirectoryError, PermissionError, OSError) as e:
            logger.error(f"Error writing file '{path}': {e}")
            return _format_error("write_file", path, str(e))
        except Exception as e:
             logger.exception(f"Unexpected error writing file '{path}'")
             return _format_error("write_file", path, f"Unexpected error: {e}")

    # --- edit_file: Manual Definition ---
    async def edit_file(path: str, edits: List[Dict[str, str]], dry_run: bool) -> str:
        """
        (Async) Edits a text file by applying a list of sequential text replacements.
        Returns a git-style diff of the changes. If dry_run is True, changes are not saved.

        Args:
            path: The relative path to the file within the allowed directory.
            edits: A list of dictionaries, each with 'old_text' and 'new_text' keys.
                   Replacements are applied sequentially based on the file content *after* the previous edit.
                   Each 'old_text' is replaced only once per edit step.
            dry_run: If True, performs a dry run showing the diff without saving changes.

        Returns:
            A git-style diff of the proposed changes and a status message, or an error message starting with 'Error:'.
        """
        logger.info(f"Tool executed: edit_file (Path: {path}, Dry Run: {dry_run}, Edits: {len(edits)})")
        try:
            # Using asyncio.to_thread to run synchronous file I/O in a separate thread
            # This is important because the underlying Path methods are sync
            valid_path = await asyncio.to_thread(_validate_path, path, check_existence=True, check_is_dir=False)
            original_content = await asyncio.to_thread(valid_path.read_text, encoding='utf-8')
            original_content_lines = original_content.splitlines()
            current_content_str = "\n".join(original_content_lines)

            applied_changes_count = 0
            errors = []

            for i, edit in enumerate(edits):
                old_text = edit.get('old_text')
                new_text = edit.get('new_text')

                if old_text is None or new_text is None:
                    msg = f"Edit {i+1}: Skipped due to missing 'old_text' or 'new_text'."
                    errors.append(msg)
                    logger.warning(f"Edit File '{path}': {msg}")
                    continue

                if old_text in current_content_str:
                    current_content_str = current_content_str.replace(old_text, new_text, 1)
                    applied_changes_count += 1
                    logger.debug(f"Edit File '{path}': Applied edit {i+1}.")
                else:
                    msg = f"Edit {i+1}: Skipped as exact 'old_text' was not found in the current content state."
                    errors.append(msg)
                    logger.warning(f"Edit File '{path}': {msg} (Old text: '{old_text[:50]}...')")

            modified_content_lines = current_content_str.splitlines()

            diff = list(difflib.unified_diff(
                original_content_lines,
                modified_content_lines,
                fromfile=f"a/{path}",
                tofile=f"b/{path}",
                lineterm='\n'
            ))
            diff_str = "".join(diff) if diff else "No changes detected."

            result_message = f"Proposed changes for '{path}':\n```diff\n{diff_str}\n```\n"

            if errors:
                result_message += f"\nStatus: Completed with {len(errors)} issue(s):\n- " + "\n- ".join(errors)

            if not dry_run and applied_changes_count > 0:
                try:
                    # Run sync file write in thread
                    await asyncio.to_thread(valid_path.write_text, current_content_str, encoding='utf-8')
                    status = f"Successfully applied {applied_changes_count} edit(s) and saved the file."
                    result_message += f"\nStatus: {status}"
                    logger.info(f"Edit File '{path}': {status}")
                except (PermissionError, OSError) as e:
                    logger.error(f"Error saving edited file '{path}': {e}", exc_info=True)
                    return f"Error: Failed to save edited file '{path}': {e}"
            elif not dry_run and applied_changes_count == 0:
                 status = "No changes were applied (either 'old_text' not found or edits resulted in no change). File not saved."
                 result_message += f"\nStatus: {status}"
            elif dry_run:
                 status = f"Dry run complete. {applied_changes_count} edit(s) would be applied. File not saved."
                 result_message += f"\nStatus: {status}"

            return result_message

        except (ValidationException, FileNotFoundError, IsADirectoryError, PermissionError, UnicodeDecodeError) as e:
            logger.error(f"Error preparing to edit file '{path}': {e}", exc_info=True)
            return f"Error: Cannot edit file '{path}': {e}"
        except Exception as e:
            logger.exception(f"Unexpected error editing file '{path}': {e}")
            return f"Error: Unexpected error editing file '{path}': {e}"

    # Wrapper for FunctionTool invocation
    async def invoke_edit_file(ctx: RunContextWrapper[Any], args: str) -> str:
        try:
            parsed_args = json.loads(args)
            path = parsed_args.get("path")
            edits = parsed_args.get("edits")
            dry_run = parsed_args.get("dry_run", False) # Default dry_run to False if not provided

            if not path or not edits or dry_run is None:
                 logger.error(f"invoke_edit_file missing required arguments in: {args}")
                 return "Error: Missing required arguments for edit_file (path, edits, dry_run)."

            # Type check for edits
            if not isinstance(edits, list) or not all(isinstance(e, dict) for e in edits):
                logger.error(f"invoke_edit_file received invalid type for 'edits': {type(edits)}")
                return "Error: Invalid format for 'edits' argument. Expected a list of dictionaries."

            return await edit_file(path=path, edits=edits, dry_run=dry_run)
        except json.JSONDecodeError:
            logger.error(f"invoke_edit_file failed to decode JSON arguments: {args}", exc_info=True)
            return f"Error: Invalid arguments format for edit_file: {args}"
        except Exception as e:
            logger.exception(f"Unexpected error invoking edit_file with args: {args}")
            return f"Error: Unexpected error calling edit_file: {e}"

    # Define the JSON schema manually
    edit_file_params_schema = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The relative path to the file within the allowed directory."
            },
            "edits": {
                "type": "array",
                "description": "A list of dictionaries, each with 'old_text' and 'new_text' keys. Replacements are applied sequentially. Each 'old_text' is replaced only once per edit step.",
                "items": {
                    "type": "object",
                    "properties": {
                        "old_text": {"type": "string"},
                        "new_text": {"type": "string"}
                    },
                    "required": ["old_text", "new_text"],
                    "additionalProperties": False # Disallow extra properties in edit items
                }
            },
            "dry_run": {
                "type": "boolean",
                "description": "If True, performs a dry run showing the diff without saving changes."
            }
        },
        "required": ["path", "edits", "dry_run"],
        "additionalProperties": False # Disallow extra properties in the main parameters object
    }

    # Create the FunctionTool instance
    edit_file_tool = FunctionTool(
        name="edit_file",
        description="Edits a text file by applying a list of sequential text replacements. Returns a git-style diff.",
        params_json_schema=edit_file_params_schema,
        on_invoke_tool=invoke_edit_file,
    )

    @function_tool
    def create_directory(path: str) -> str:
        """
        Creates a directory (including any necessary parent directories) at the specified relative path.
        Succeeds silently if the directory already exists.

        Args:
            path: The relative path for the new directory.

        Returns:
            A confirmation message or an error message starting with 'Error:'.
        """
        logger.info(f"Tool executed: create_directory (Path: {path})")
        try:
            valid_path = _validate_path(path, check_existence=False, allow_create=True)
            valid_path.mkdir(parents=True, exist_ok=True)
            if not valid_path.is_dir():
                raise FileExistsError(f"Path exists but is not a directory: {path}")
            logger.info(f"Successfully ensured directory exists: {valid_path}")
            return f"Directory '{path}' created or already exists."
        except (ValidationException, FileExistsError, PermissionError, OSError) as e:
            logger.error(f"Error creating directory '{path}': {e}")
            return _format_error("create_directory", path, str(e))
        except Exception as e:
             logger.exception(f"Unexpected error creating directory '{path}'")
             return _format_error("create_directory", path, f"Unexpected error: {e}")

    @function_tool
    def list_directory(path: str) -> str:
        """
        Lists the contents (files and subdirectories) of a specified directory.
        Prefixes directories with '[DIR]' and files with '[FILE]'.

        Args:
            path: The relative path to the directory. Use '.' for the base directory.

        Returns:
            A string listing the directory contents, or an error message starting with 'Error:'.
        """
        logger.info(f"Tool executed: list_directory (Path: {path})")
        try:
            valid_path = _validate_path(path, check_existence=True, check_is_dir=True)
            entries = []
            try:
                for entry in sorted(valid_path.iterdir(), key=lambda p: p.name):
                    prefix = "[DIR] " if entry.is_dir() else "[FILE]"
                    entries.append(f"{prefix} {entry.name}")
            except PermissionError as pe:
                 logger.warning(f"Permission denied iterating directory '{path}': {pe}")
                 return _format_error("list_directory", path, f"Permission denied to list contents: {pe}")

            logger.info(f"Successfully listed directory: {valid_path}")
            if not entries:
                return f"Directory '{path}' is empty."
            return f"Contents of '{path}':\n" + "\n".join(entries)
        except (ValidationException, FileNotFoundError, NotADirectoryError, PermissionError) as e:
            logger.error(f"Error listing directory '{path}': {e}")
            return _format_error("list_directory", path, str(e))
        except Exception as e:
             logger.exception(f"Unexpected error listing directory '{path}'")
             return _format_error("list_directory", path, f"Unexpected error: {e}")

    @function_tool
    def directory_tree(path: str) -> str:
        """
        Generates a string representation of the directory structure starting from the specified path.
        Only includes accessible files and directories within the allowed scope.

        Args:
            path: The relative path to the root directory for the tree view. Use '.' for the base directory.

        Returns:
            A string representing the directory tree, or an error message.
        """
        logger.info(f"Tool executed: directory_tree (Path: {path})")
        try:
            valid_root_path = _validate_path(path, check_existence=True, check_is_dir=True)

            def build_tree(current_path: Path, prefix: str = "") -> List[str]:
                tree: List[str] = []
                try:
                    for entry in sorted(current_path.iterdir(), key=lambda p: p.name):
                        if settings.ALLOWED_BASE_DIR_RESOLVED:
                            entry_relative_path_str = str(entry.relative_to(settings.ALLOWED_BASE_DIR_RESOLVED))
                            try:
                                entry_valid_path = _validate_path(entry_relative_path_str, check_existence=True)
                                entry_name = entry.name
                                tree.append(f"{prefix}- {entry_name}{'/' if entry_valid_path.is_dir() else ''}")
                                if entry_valid_path.is_dir():
                                    children = build_tree(entry_valid_path, prefix + "  |")
                                    tree.extend(children)
                            except (ValidationException, FileNotFoundError, PermissionError) as ve:
                                logger.warning(f"Skipping entry '{entry.name}' in tree view for '{path}': {ve}")
                            except Exception as inner_e:
                                logger.error(f"Error processing entry '{entry.name}' in tree view for '{path}': {inner_e}", exc_info=True)
                except PermissionError as pe:
                    logger.warning(f"Permission denied reading directory '{current_path}' for tree view: {pe}")
                    tree.append(f"{prefix}- Error accessing {current_path.name}: Permission Denied")
                except Exception as e:
                    logger.error(f"Error iterating directory {current_path} for tree: {e}", exc_info=True)
                    tree.append(f"{prefix}- Error iterating {current_path.name}: {str(e)}")
                return tree

            tree_data = build_tree(valid_root_path)
            logger.info(f"Successfully generated directory tree for: {valid_root_path}")
            if not tree_data:
                return f"Directory '{path}' is empty or inaccessible."
            return f"Directory tree for '{path}':\n" + "\n".join(tree_data)

        except (ValidationException, FileNotFoundError, NotADirectoryError, PermissionError) as e:
            logger.error(f"Error generating directory tree for '{path}': {e}")
            return _format_error("directory_tree", path, str(e))
        except Exception as e:
            logger.exception(f"Unexpected error generating directory tree for '{path}'")
            return _format_error("directory_tree", path, f"Unexpected error: {e}")

    @function_tool
    def move_file(source: str, destination: str) -> str:
        """
        Moves or renames a file or directory from source to destination.
        Both paths must be relative and within the allowed directory.
        Fails if the destination path already exists.

        Args:
            source: The relative source path.
            destination: The relative destination path.

        Returns:
            A confirmation message or an error message starting with 'Error:'.
        """
        logger.info(f"Tool executed: move_file (Source: {source}, Destination: {destination})" )
        try:
            valid_source = _validate_path(source, check_existence=True)
            valid_dest = _validate_path(destination, check_existence=False, allow_create=True)

            if valid_dest.exists():
                 raise FileExistsError(f"Destination path '{destination}' already exists.")

            dest_parent = valid_dest.parent
            if not dest_parent.exists():
                raise FileNotFoundError(f"Parent directory for destination '{destination}' does not exist.")
            if not dest_parent.is_dir():
                 raise NotADirectoryError(f"Parent path for destination '{destination}' is not a directory.")

            shutil.move(str(valid_source), str(valid_dest))
            logger.info(f"Successfully moved '{valid_source}' to '{valid_dest}'")
            return f"Successfully moved '{source}' to '{destination}'."
        except (ValidationException, FileNotFoundError, FileExistsError, NotADirectoryError, PermissionError, OSError) as e:
            logger.error(f"Error moving '{source}' to '{destination}': {e}")
            return _format_error("move_file", source, str(e))
        except Exception as e:
             logger.exception(f"Unexpected error moving '{source}' to '{destination}'")
             return _format_error("move_file", source, f"Unexpected error: {e}")

    @function_tool
    def search_files(path: str, pattern: str, case_sensitive: bool) -> str:
        """
        Recursively searches for files/directories matching a glob pattern within a specified path.

        Args:
            path: The relative path to start the search from. Use '.' for the base directory.
            pattern: The glob pattern (e.g., '*.txt', 'data/**/log?.csv'). Case sensitivity depends on the 'case_sensitive' flag.
            case_sensitive: If True, matching is case-sensitive. If False, it's case-insensitive (may be slower).

        Returns:
            A list of matching relative paths (from the search root), or a 'No matches found' message, or an error message starting with 'Error:'.
        """
        logger.info(f"Tool executed: search_files (Path: {path}, Pattern: {pattern}, Case Sensitive: {case_sensitive})")
        try:
            valid_path = _validate_path(path, check_existence=True, check_is_dir=True)
            results = []

            logger.debug(f"Searching with pattern '{pattern}' in '{valid_path}'. Case sensitive: {case_sensitive}")
            if case_sensitive:
                matched_paths = valid_path.rglob(pattern)
            else:
                # Manual case-insensitive glob might be needed for true cross-platform behavior
                # This simplified version relies on OS behavior for Path.rglob
                # Consider using fnmatch if precise control is needed
                pattern_lower = pattern.lower()
                matched_paths = (p for p in valid_path.rglob('*') if p.name.lower().endswith(pattern_lower.lstrip('*'))) # Basic example

            processed_count = 0
            for p in matched_paths:
                processed_count += 1
                try:
                    if settings.ALLOWED_BASE_DIR_RESOLVED:
                        relative_to_base = p.relative_to(settings.ALLOWED_BASE_DIR_RESOLVED)
                        _validate_path(str(relative_to_base))
                        relative_to_search_root = p.relative_to(valid_path)
                        results.append(str(relative_to_search_root))
                    else:
                        logger.error("Base directory not resolved, cannot validate search result path.")
                        continue
                except (ValidationException, PermissionError) as ve:
                    logger.warning(f"Search result '{p.name}' skipped: {ve}")
                except Exception as inner_e:
                    logger.warning(f"Could not process search result '{p.name}': {inner_e}")

            logger.info(f"Search completed. Processed {processed_count} potential matches, found {len(results)} valid results for pattern '{pattern}' in '{path}'.")
            if not results:
                return f"No matches found for pattern '{pattern}' in directory '{path}'."
            results.sort()
            return f"Search results for '{pattern}' in '{path}':\n" + "\n".join(results)
        except (ValidationException, FileNotFoundError, NotADirectoryError, PermissionError) as e:
            logger.error(f"Error searching files in '{path}': {e}")
            return _format_error("search_files", path, str(e))
        except Exception as e:
            logger.exception(f"Unexpected error searching files in '{path}'")
            return _format_error("search_files", path, f"Unexpected error: {e}")

    @function_tool
    def get_file_info(path: str) -> str:
        """
        Retrieves metadata (type, size, modified time, permissions) about a file or directory.

        Args:
            path: The relative path to the file or directory.

        Returns:
            A string containing metadata, or an error message starting with 'Error:'.
        """
        logger.info(f"Tool executed: get_file_info (Path: {path})")
        try:
            valid_path = _validate_path(path, check_existence=True)
            stats = valid_path.stat()
            info = {
                "Path": path,
                "Type": "Directory" if valid_path.is_dir() else "File",
                "Size (bytes)": stats.st_size,
                "Last Modified (UTC)": datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc).isoformat(),
                "Permissions (octal)": oct(stats.st_mode & 0o777),
            }
            logger.info(f"Successfully retrieved info for: {valid_path}")
            info_str = "\n".join([f"- {k}: {v}" for k, v in info.items()])
            return f"Information for '{path}':\n{info_str}"
        except (ValidationException, FileNotFoundError, PermissionError) as e:
            logger.error(f"Error getting info for '{path}': {e}")
            return _format_error("get_file_info", path, str(e))
        except Exception as e:
            logger.exception(f"Unexpected error getting info for '{path}'")
            return _format_error("get_file_info", path, f"Unexpected error: {e}")

else:
    def _format_error(tool_name: str, path: Optional[str], message: str) -> str:
        """Formats consistent error messages when SDK is unavailable."""
        prefix = f"Error in {tool_name}"
        if path:
            prefix += f" for '{path}'"
        return f"{prefix}: {message} (Reason: OpenAI Agents SDK not installed)"

    def list_allowed_directory() -> str: return _format_error("list_allowed_directory", None, "Operation failed")
    def read_file(path: str) -> str: return _format_error("read_file", path, "Operation failed")
    def read_multiple_files(paths: List[str]) -> str: return _format_error("read_multiple_files", None, "Operation failed")
    def write_file(path: str, content: str) -> str: return _format_error("write_file", path, "Operation failed")

    # Placeholder for edit_file that matches FunctionTool structure
    async def placeholder_invoke_edit_file(ctx: Any, args: str) -> str: # Match invoke_edit_file signature
         """Placeholder invocation function for edit_file when SDK is unavailable."""
         path_info = ""
         try:
             # Attempt to parse args to get path for a slightly better error message
             parsed_args = json.loads(args)
             path_info = parsed_args.get("path", "")
         except:
             pass # Ignore errors in parsing placeholder args
         return _format_error("edit_file", path_info or None, "Operation failed")

    # Create a placeholder object mimicking FunctionTool structure
    class PlaceholderEditFileTool:
         name="edit_file"
         description="Placeholder edit_file tool (SDK not available)"
         params_json_schema: Dict[str, Any] ={}
         # Assign the async placeholder invocation function
         on_invoke_tool=placeholder_invoke_edit_file

    edit_file_tool = PlaceholderEditFileTool() # Assign placeholder instance

    def create_directory(path: str) -> str: return _format_error("create_directory", path, "Operation failed")
    def list_directory(path: str) -> str: return _format_error("list_directory", path, "Operation failed")
    def directory_tree(path: str) -> str: return _format_error("directory_tree", path, "Operation failed")
    def move_file(source: str, destination: str) -> str: return _format_error("move_file", source, "Operation failed")
    def search_files(path: str, pattern: str, case_sensitive: bool) -> str: return _format_error("search_files", path, "Operation failed")
    def get_file_info(path: str) -> str: return _format_error("get_file_info", path, "Operation failed")

filesystem_tools_list = [
    list_allowed_directory,
    read_file,
    read_multiple_files,
    write_file,
    edit_file_tool, # Use the manually created tool instance
    create_directory,
    list_directory,
    directory_tree,
    move_file,
    search_files,
    get_file_info,
]