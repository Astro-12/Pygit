import os
import zlib
from pygit.index import read_index


HEAD_FILE = ".pygit/HEAD"
OBJECTS_DIR = ".pygit/objects"
REFS_DIR = ".pygit/refs"


def read_head():
    """Read .pygit/HEAD and resolve to a commit SHA.

    Returns the 40-char hex SHA-1 of the current HEAD commit,
    or None if no commits exist yet.
    """
    if not os.path.exists(HEAD_FILE):
        return None

    with open(HEAD_FILE, "r") as f:
        content = f.read().strip()

    if content.startswith("ref: "):
        ref_path = content[len("ref: "):]
        full_ref = os.path.join(".pygit", ref_path)
        if not os.path.exists(full_ref):
            return None
        with open(full_ref, "r") as f:
            return f.read().strip()

    return content if content else None


def read_object(sha1):
    """Read and decompress a raw git object by SHA-1 hash.

    Returns (type_str, content_bytes) e.g. ("blob", b"...").
    """
    obj_file = os.path.join(OBJECTS_DIR, sha1[:2], sha1[2:])
    if not os.path.exists(obj_file):
        return None, None

    with open(obj_file, "rb") as f:
        compressed = f.read()

    full_data = zlib.decompress(compressed)
    header, content = full_data.split(b"\0", 1)
    obj_type = header.split(b" ")[0].decode("utf-8")
    return obj_type, content


def read_commit(sha1):
    """Parse a commit object into its components.

    Returns dict with keys: tree, parent, author, committer, message.
    """
    obj_type, content = read_object(sha1)
    if obj_type != "commit":
        return None

    text = content.decode("utf-8")
    lines = text.split("\n")

    result = {
        "tree": None,
        "parent": None,
        "author": None,
        "committer": None,
        "message": "",
    }

    blank_idx = len(lines)
    for i, line in enumerate(lines):
        if line == "":
            blank_idx = i
            break
        if line.startswith("tree "):
            result["tree"] = line[5:]
        elif line.startswith("parent "):
            result["parent"] = line[7:]
        elif line.startswith("author "):
            result["author"] = line[7:]
        elif line.startswith("committer "):
            result["committer"] = line[10:]

    result["message"] = "\n".join(lines[blank_idx + 1:]).strip()
    return result


def read_tree(sha1, prefix=""):
    """Recursively parse a tree object.

    Returns dict mapping relative file paths to blob SHA-1 hashes.
    Subdirectories are traversed recursively, building full relative paths.
    """
    obj_type, content = read_object(sha1)
    if obj_type != "tree":
        return {}

    result = {}
    i = 0
    while i < len(content):
        # Find the space between mode and name
        space_idx = content.index(b" ", i)
        mode = content[i:space_idx].decode("utf-8")

        # Find the null byte after the name
        null_idx = content.index(b"\0", space_idx)
        name = content[space_idx + 1:null_idx].decode("utf-8")

        # Read the 20-byte binary SHA-1
        sha_bytes = content[null_idx + 1:null_idx + 21]
        entry_sha = sha_bytes.hex()

        # Move past this entry
        i = null_idx + 21

        full_path = prefix + name
        if mode == "40000":
            # Subdirectory - recurse
            sub_result = read_tree(entry_sha, full_path + "/")
            result.update(sub_result)
        else:
            result[full_path] = entry_sha

    return result


def get_workdir_files(directory="."):
    """Scan working directory and return dict of path -> stat info.

    Returns dict: {relative_path: os.stat_result}
    Excludes .pygit/ and .git/ directories.
    """
    result = {}
    for root, dirs, files in os.walk(directory):
        # Skip hidden/git directories
        dirs[:] = [d for d in dirs if d not in (".pygit", ".git")]

        for fname in files:
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, directory)
            result[rel_path] = os.stat(full_path)

    return result


def is_modified(index_entry, workdir_stat):
    """Check if a file has been modified since it was staged.

    Uses quick heuristic: compare size and mtime from the index
    against current stat on disk.
    """
    return (
        index_entry["size"] != workdir_stat.st_size
        or index_entry["mtime"] != workdir_stat.st_mtime
    )


def status():
    """Display the status of the working tree.

    Compares three states: HEAD (last commit), Index (staging area),
    and Working Directory (files on disk).
    """
    head_sha = read_head()
    index_entries = read_index()

    # Build index lookup: {path: entry_dict}
    index_files = {}
    for entry in index_entries:
        index_files[entry["path"]] = entry

    # Get working directory files
    workdir_files = get_workdir_files()

    # If no commits yet, HEAD tree is empty
    head_files = {}
    if head_sha:
        commit = read_commit(head_sha)
        if commit and commit["tree"]:
            head_files = read_tree(commit["tree"])

    # --- Compare HEAD vs Index (staged changes) ---
    staged_added = []
    staged_modified = []
    staged_deleted = []

    for path in index_files:
        if path not in head_files:
            staged_added.append(path)
        elif index_files[path]["sha1"] != head_files[path]:
            staged_modified.append(path)

    for path in head_files:
        if path not in index_files:
            staged_deleted.append(path)

    # --- Compare Index vs Working Directory (unstaged changes) ---
    unstaged_modified = []
    unstaged_deleted = []

    for path, entry in index_files.items():
        if path not in workdir_files:
            unstaged_deleted.append(path)
        elif is_modified(entry, workdir_files[path]):
            unstaged_modified.append(path)

    # --- Untracked files ---
    untracked = []
    for path in workdir_files:
        if path not in index_files:
            untracked.append(path)

    # --- Print output ---
    print(f"On branch main")

    has_staged = staged_added or staged_modified or staged_deleted
    has_unstaged = unstaged_modified or unstaged_deleted
    has_untracked = untracked

    if has_staged:
        print("\nChanges to be committed:")
        for p in sorted(staged_added):
            print(f"\tnew file:   {p}")
        for p in sorted(staged_modified):
            print(f"\tmodified:   {p}")
        for p in sorted(staged_deleted):
            print(f"\tdeleted:    {p}")

    if has_unstaged:
        print("\nChanges not staged for commit:")
        for p in sorted(unstaged_modified):
            print(f"\tmodified:   {p}")
        for p in sorted(unstaged_deleted):
            print(f"\tdeleted:    {p}")

    if has_untracked:
        print("\nUntracked files:")
        for p in sorted(untracked):
            print(f"\t{p}")

    if not has_staged and not has_unstaged and not has_untracked:
        print("\nnothing to commit, working tree clean")
