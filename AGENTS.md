# AGENTS.md — PyGit Project Guidelines

## Project Overview
PyGit is a lightweight Python implementation of Git's core plumbing commands. It demonstrates how Git works as a content-addressable key-value store using SHA-1 hashing and zlib compression.

## Repository Structure
- `pygit.py` — Main entry point and CLI. Contains: init, hash-object, cat-file, write-tree, commit-tree (incomplete)
- `pygit/index.py` — Index (staging area) system using JSON format
- `pygit/status.py` — Status implementation: read HEAD, parse commits, parse trees, compare working dir vs index vs HEAD
- `main.py` — Unused (empty)

## Architecture
```
Working Directory → Index (staging area) → Commit (tree → blob objects)
                                                ↓
                                          refs/heads/<branch> (branch pointer)
                                                ↓
                                               HEAD (symbolic ref)
```

## Implemented Commands
| Command | Status | Location |
|---------|--------|----------|
| `init` | ✅ Complete | `pygit.py:7` |
| `hash-object` | ✅ Complete | `pygit.py:17` |
| `cat-file` | ✅ Complete | `pygit.py:33` |
| `write-tree` | ✅ Complete | `pygit.py:46` |
| `commit-tree` | ⚠️ Incomplete | `pygit.py:112` — missing disk write, outside __main__ |

## Implemented Internals
- **Index system** (`pygit/index.py`): JSON-based staging area with `read_index`, `write_index`, `add_to_index`, `add_directory`
- **Object reading** (`pygit/status.py`): `read_object`, `read_commit`, `read_tree` — full parsing of git objects
- **Status** (`pygit/status.py`): Three-way comparison (HEAD vs index vs working dir)

## Known Bugs
1. `has_objects` should be `hash_objects` (typo)
2. `commit_tree` is outside `if __name__ == "__main__"` — unreachable from CLI
3. `commit_tree` computes SHA-1 but never writes the object to disk
4. `hash-object` header format missing space: `"blob{len(data)}"` should be `"blob {len(data)}"`

## What's Missing
- Wire `commit_tree` to CLI
- Complete `commit_tree` (write object to disk, return sha1)
- `add` command (call index.add_directory)
- `commit` command (orchestrate: index → tree → commit → update-ref)
- `log` command (walk commit chain)
- `update_ref` function (write SHA to refs/heads/<branch>)
- Branch management (`branch`, `checkout`)

## Code Conventions
- Python 3.6+, standard library only
- Single-file entry point (`pygit.py`) for CLI
- Modular internals in `pygit/` package
- Functions prefixed with `read_` / `write_` for I/O operations
- SHA-1 hashes stored as 40-character hex strings

## Testing
- Manual testing: run commands and verify output
- Example workflow:
  ```bash
  python pygit.py init
  echo "hello" > test.txt
  python pygit.py hash-object test.txt
  python pygit.py write-tree
  ```

## Dependencies
- Python 3.6+
- Standard library only: `os`, `sys`, `hashlib`, `time`, `zlib`, `json`
