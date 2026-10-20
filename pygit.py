import os
import sys
import hashlib
import zlib
import time
import json
from pygit.index import add_directory, read_index
from pygit.status import read_commit, read_object, status

# -------------------------------------------------------------------
# Core Git Plumbing Functions
# -------------------------------------------------------------------

def init():
    os.makedirs(".git/objects", exist_ok=True)
    os.makedirs(".git/refs/heads", exist_ok=True)
    with open(".git/HEAD", "w") as f:
        f.write("ref: refs/heads/main\n")
    print("Initialized empty PyGit repository in .git/")

#this funtion takes a file path as input, reads the file content
#then it creates a blob object by creating a header with file size and type
#Then it compresses it and stores it in the .git/objects directory and returns the sha1 hash of object

def hash_object(filepath, write=True):
    with open(filepath, "rb") as f:
        data = f.read()
    header = f"blob {len(data)}\0".encode()
    store = header + data
    sha1 = hashlib.sha1(store).hexdigest()
    
    if write:
        obj_dir = os.path.join(".git/objects", sha1[:2])
        os.makedirs(obj_dir, exist_ok=True)
        obj_path = os.path.join(obj_dir, sha1[2:])
        with open(obj_path, "wb") as f:
            f.write(zlib.compress(store))
            
    return sha1

#this function takes the sha1 hash of an object read the sha1 hash and decompresses the object file
#then it splits the header and content and returns the object type and content
def cat_file(sha1):
    obj_dir = sha1[:2]
    obj_file = sha1[2:]
    filepath = os.path.join(".git/objects", obj_dir, obj_file)
    
    with open(filepath, "rb") as f:
        data = zlib.decompress(f.read())
        
    header, content = data.split(b"\0", 1)
    sys.stdout.buffer.write(content)

def write_tree():
    """Writes current index tree to object database and returns tree SHA-1."""
    index = read_index()
    tree_entries = []
    
    for entry in sorted(index, key=lambda e: e["path"]):
        path = entry["path"]
        sha1 = entry["sha1"]
        mode = entry.get("mode", "100644")
        entry_bytes = f"{mode} {path}\0".encode() + bytes.fromhex(sha1)
        tree_entries.append(entry_bytes)
        
    tree_data = b"".join(tree_entries)
    header = f"tree {len(tree_data)}\0".encode()
    store = header + tree_data
    sha1 = hashlib.sha1(store).hexdigest()
    
    obj_dir = os.path.join(".git/objects", sha1[:2])
    os.makedirs(obj_dir, exist_ok=True)
    obj_path = os.path.join(obj_dir, sha1[2:])
    
    with open(obj_path, "wb") as f:
        f.write(zlib.compress(store))
        
    return sha1

#this function takes the sha1 hash of a commit object and then it reads the commit object file
#then it splits the header and content and then it parses the content to extract the commit information
def commit_tree(tree_sha, message, parent=None):
    """Creates a commit object and writes it to disk."""
    lines = [f"tree {tree_sha}"]
    if parent:
        lines.append(f"parent {parent}")
        
    timestamp = int(time.time())
    utc_offset = "+0000"
    author = f"PyGit User <user@pygit.local> {timestamp} {utc_offset}"
    
    lines.append(f"author {author}")
    lines.append(f"committer {author}")
    lines.append("")
    lines.append(message)
    
    content = "\n".join(lines).encode()
    header = f"commit {len(content)}\0".encode()
    store = header + content
    sha1 = hashlib.sha1(store).hexdigest()
    
    obj_dir = os.path.join(".git/objects", sha1[:2])
    os.makedirs(obj_dir, exist_ok=True)
    obj_path = os.path.join(obj_dir, sha1[2:])
    
    with open(obj_path, "wb") as f:
        f.write(zlib.compress(store))
        
    return sha1

#this function takes a sha1 hash of an object and then it reads the object 
#
def update_ref(ref_path, sha1):
    """Updates active reference pointer to target SHA-1."""
    full_path = os.path.join(".git", ref_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(f"{sha1}\n")

def get_head_sha():
    """Resolves HEAD to current commit SHA-1 if present."""
    head_path = ".git/HEAD"
    if not os.path.exists(head_path):
        return None
        
    with open(head_path, "r") as f:
        ref = f.read().strip()
        
    if ref.startswith("ref: "):
        ref_path = os.path.join(".git", ref[5:])
        if os.path.exists(ref_path):
            with open(ref_path, "r") as rf:
                return rf.read().strip()
    return None

def get_head_ref():
    """Gets current HEAD symbolic reference path."""
    with open(".git/HEAD", "r") as f:
        ref = f.read().strip()
    return ref[5:] if ref.startswith("ref: ") else None

# -------------------------------------------------------------------
# High-Level Commands
# -------------------------------------------------------------------

def add_cmd(path="."):
    add_directory(path, hash_fn=hash_object)
    print(f"Staged files from '{path}'")

def commit_cmd(message):
    tree_sha = write_tree()
    parent_sha = get_head_sha()
    commit_sha = commit_tree(tree_sha, message, parent=parent_sha)
    
    head_ref = get_head_ref()
    if head_ref:
        update_ref(head_ref, commit_sha)
    else:
        with open(".git/HEAD", "w") as f:
            f.write(f"{commit_sha}\n")
            
    print(f"[{head_ref or 'detached HEAD'} {commit_sha[:7]}] {message}")

def log_cmd():
    current_sha = get_head_sha()
    if not current_sha:
        print("No commits yet.")
        return
        
    while current_sha:
        obj_type, data = read_object(current_sha)
        if obj_type != "commit":
            break
            
        commit_info = read_commit(current_sha)
        print(f"commit {current_sha}")
        if "author" in commit_info:
            print(f"Author: {commit_info['author']}")
        print(f"\n    {commit_info['message']}\n")
        
        current_sha = commit_info.get("parent")

# -------------------------------------------------------------------
# CLI Entry Point
# -------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pygit.py <command> [<args>]")
        sys.exit(1)
        
    cmd = sys.argv[1]
    
    if cmd == "init":
        init()
    elif cmd == "add":
        target = sys.argv[2] if len(sys.argv) > 2 else "."
        add_cmd(target)
    elif cmd == "hash-object":
        print(hash_object(sys.argv[2]))
    elif cmd == "cat-file":
        cat_file(sys.argv[2])
    elif cmd == "write-tree":
        print(write_tree())
    elif cmd == "commit-tree":
        tree_sha = sys.argv[2]
        msg = sys.argv[4] if len(sys.argv) > 4 and sys.argv[3] == "-m" else "Commit"
        print(commit_tree(tree_sha, msg))
    elif cmd == "commit":
        msg = sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == "-m" else "Initial commit"
        commit_cmd(msg)
    elif cmd == "log":
        log_cmd()
    elif cmd == "status":
        status()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)