# pygit Fix Report

## Overview
This report details the bugs found and fixed in the pygit project. The fixes ensure proper functioning of the `add` command and index management system.

---

## Bugs Fixed

### Bug 1: Indentation Error in `add_directory()` (index.py:42)

**Original Code:**
```python
def add_directory(directory: str = '.', hash_fn=None):
    for root,dirs, files in os.walk(directory):
        if ".pygit" in dirs:
            dirs.remove(".pygit")  #skip .pygit directory
            for file in files:  # ← WRONG: indented inside if block
                filepath = os.path.join(root, file)
                blob_sha1 = hash_fn(filepath, write=True)
                add_to_index(filepath, blob_sha1)
```

**Fixed Code:**
```python
def add_directory(directory: str = '.', hash_fn=None):
    for root, dirs, files in os.walk(directory):
        if ".pygit" in dirs:
            dirs.remove(".pygit")  #skip .pygit directory
        for file in files:  # ← CORRECT: at same level as if
            filepath = os.path.join(root, file)
            blob_sha1 = hash_fn(filepath, write=True)
            add_to_index(filepath, blob_sha1)
```

**Why it was broken:** The `for file in files` loop was inside the `if ".pygit" in dirs` block. This meant files were only processed when the current directory contained a `.pygit` folder. In most cases, this meant files were never added to the index.

**Impact:** Without this fix, `add_directory()` would silently fail to add any files to the index unless the directory happened to contain a `.pygit` folder.

---

### Bug 2: Wrong Return Type in `read_index()` (index.py:11)

**Original Code:**
```python
def read_index():
    if not os.path.exists(INDEX_FILE):
        return {}  # ← Returns empty dict
```

**Fixed Code:**
```python
def read_index():
    if not os.path.exists(INDEX_FILE):
        return []  # ← Returns empty list
```

**Why it was broken:** The function returned an empty dict `{}` when the index didn't exist, but `add_to_index()` treated the result as a list (used list comprehension and `.append()`). This would cause a `TypeError` when trying to add the first file to a new index.

**Impact:** Without this fix, the first call to `add_to_index()` would crash with a TypeError.

---

### Bug 3: Missing `__init__.py`

**Added:** `pygit/__init__.py` (empty file)

**Why it was broken:** The `pygit/` directory existed but had no `__init__.py` file, making it an invalid Python package. When `main.py` tried to `from pygit.index import ...`, Python couldn't find the module.

**Impact:** Without this fix, all imports from `pygit.index` would fail with `ModuleNotFoundError`.

---

### Bug 4: Missing Imports in `main.py`

**Added:**
```python
from pygit.index import read_index, add_to_index, add_directory
```

**Why it was broken:** `main.py` didn't import any functions from `pygit/index.py`, so the `add` command and index operations couldn't work.

**Impact:** Without this fix, the `add` command would fail with `NameError` when trying to call index functions.

---

### Bug 5: Missing `add` Command in CLI

**Added to `if __name__ == "__main__"`:**
```python
elif command == "add":
    target = sys.argv[2] if len(sys.argv) > 2 else "."
    if os.path.isfile(target):
        blob_sha = has_objects(target, write=True)
        add_to_index(target, blob_sha)
        print(f"Added {target}")
    elif os.path.isdir(target):
        add_directory(target, hash_fn=has_objects)
        print(f"Added {target}")
    else:
        print(f"File or directory '{target}' not found.")
```

**Why it was broken:** The CLI had no `add` command, so users couldn't stage files. The `add` functionality existed in `pygit/index.py` but wasn't accessible from the command line.

**Impact:** Without this fix, users had no way to use the staging area functionality.

---

### Bug 6: `write_tree()` Still Scanning Directory

**Original Behavior:** Used `os.listdir()` to scan the entire working directory every time, ignoring the index.

**Fixed Behavior:** Now reads from the index (`.pygit/index`) to create tree objects. This means:
- Only staged files are included in the tree
- The tree reflects what's in the staging area, not the entire directory
- Properly mirrors git's behavior where `write-tree` creates a tree from the index

**Why it was broken:** The original implementation bypassed the staging area entirely, making the index useless. Files had to be scanned every time, and there was no way to stage specific files.

**Impact:** Without this fix, the staging area (`add` command) had no effect on `write-tree`. The tree would always contain all files, regardless of what was staged.

---

## New Workflow

With all fixes applied, the proper workflow is now:

```bash
# Initialize repository
python main.py init

# Stage files
python main.py add file.txt        # stage single file
python main.py add .               # stage all files

# Create tree from staged files
python main.py write-tree          # returns tree SHA

# Commit the tree
python main.py commit-tree <tree_sha> "commit message"

# View commit history (not yet implemented)
# python main.py log
```

---

## Testing the Fixes

To verify the fixes work:

```bash
# 1. Initialize
python main.py init

# 2. Create a test file
echo "Hello, pygit!" > test.txt

# 3. Add to staging
python main.py add test.txt

# 4. Check the index was created
cat .pygit/index

# 5. Create tree from index
python main.py write-tree

# 6. Commit
python main.py commit-tree <tree_sha> "Initial commit"
```

---

## Next Steps

With the `add` and index system working, the next features to implement are:

1. **`status`** - Compare working tree vs index vs HEAD
2. **`log`** - Traverse commit history
3. **`diff`** - Show changes between versions
4. **`branch`** - Create and manage branches
5. **`checkout`** - Switch between branches

---

## Files Modified

| File | Changes |
|------|---------|
| `pygit/index.py` | Fixed indentation bug, fixed return type |
| `main.py` | Added imports, added `add` command, modified `write_tree()` |
| `pygit/__init__.py` | Created (empty file) |

---

## Conclusion

The core issues were:
1. **Logic errors** (indentation, return types)
2. **Missing integration** (no CLI command, no imports)
3. **Design flaw** (write-tree ignoring the index)

All fixes maintain backward compatibility while adding proper index management functionality.
