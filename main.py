import os
import sys
import hashlib
import time
import zlib
from pygit.index import read_index, add_to_index, add_directory
#init function basically does is create the directory structure for a new PyGit repository, including the
# .pygit/objects and .pygit/refs/heads directories, and initializes the HEAD file to point to the main branch.
def init():
    os.makedirs(".pygit/objects", exist_ok=True)
    os.makedirs(".pygit/refs/heads", exist_ok=True)
        
    with open(".pygit/HEAD", "w") as f:
        f.write("ref: refs/heads/main\n")
        
    print("Initialized empty PyGit repository in .pygit/")

# compresses the file and stores it in the .pygit/objects directory, returning the SHA-1 hash of the object
def has_objects(file_path, write = True):
    with open(file_path, "rb") as f:
        data = f.read()

    header = f"blob{len(data)}\0".encode("utf-8")
    full_data = header + data
    sha1 = hashlib.sha1(full_data).hexdigest()

    if write:
        obj_dir = os.path.join(".pygit","objects", sha1[:2])
        obj_file = os.path.join(obj_dir, sha1[2:])
        os.makedirs(obj_dir, exist_ok=True)
        with open(obj_file, "wb") as f:
            f.write(zlib.compress(full_data))
    return sha1
#decompresses the object file corresponding to the given SHA-1 hash and prints its content 
# to the standard output
def cat_file(sha1):
    obj_file = os.path.join(".pygit", "objects", sha1[:2], sha1[2:])
    if not os.path.exists(obj_file):
        print(f"Object {sha1} not found.")
        return

    with open(obj_file, "rb") as f:
        compressed_data = f.read()
    full_data = zlib.decompress(compressed_data)
    header, content = full_data.split(b'\0', 1)

    sys.stdout.buffer.write(content)
#creates a tree object representing the current state of the directory and its subdirectories,
# and returns the SHA-1 hash of the tree object. It recursively scans the directory,
# and for each file, it creates a blob object and adds an entry to the tree.
#  For each subdirectory, it recursively calls itself to create a tree object for that subdirectory and adds an entry to the tree.
def write_tree(directory="."):
    """Create tree objects from the index entries"""
    index_entries = read_index()
    
    # Group files by directory
    tree_map = {}  # {directory: [(filename, entry), ...]}
    for entry in index_entries:
        path = entry["path"]
        # Get relative path from the working directory
        rel_path = os.path.relpath(path, directory)
        parts = rel_path.split(os.sep)
        
        if len(parts) == 1:
            # File is in the root directory
            if directory not in tree_map:
                tree_map[directory] = []
            tree_map[directory].append((parts[0], entry))
        else:
            # File is in a subdirectory
            subdir = os.path.join(directory, parts[0])
            if subdir not in tree_map:
                tree_map[directory] = []
            tree_map[directory].append((parts[0], entry))
    
    # Build tree entries for the root directory
    tree_entries = []
    for item in sorted(os.listdir(directory)):
        if item.startswith(".pygit") or item.startswith(".git"):
            continue
        
        full_path = os.path.join(directory, item)
        
        if os.path.isfile(full_path):
            # Find this file in the index
            entry = None
            for e in index_entries:
                if os.path.relpath(e["path"], directory) == item:
                    entry = e
                    break
            
            if entry:
                sha1_bytes = bytes.fromhex(entry["sha1"])
                mode = entry.get("mode", "100644")
                name = os.path.basename(entry["path"])
                entry_bytes = f"{mode} {name}\0".encode("utf-8") + sha1_bytes
                tree_entries.append(entry_bytes)
        
        elif os.path.isdir(full_path):
            # Recursively create subtree
            subtree_sha = write_tree(full_path)
            sha1_bytes = bytes.fromhex(subtree_sha)
            mode = "40000"
            entry_bytes = f"{mode} {item}\0".encode("utf-8") + sha1_bytes
            tree_entries.append(entry_bytes)
    
    # Assemble the tree object
    tree_content = b"".join(tree_entries)
    header = f"tree {len(tree_content)}\0".encode("utf-8")
    full_data = header + tree_content
    
    sha_1 = hashlib.sha1(full_data).hexdigest()
    
    dir_name = os.path.join(".pygit", "objects", sha_1[:2])
    dir_file = os.path.join(dir_name, sha_1[2:])
    os.makedirs(dir_name, exist_ok=True)
    
    if not os.path.exists(dir_file):
        with open(dir_file, "wb") as f:
            f.write(zlib.compress(full_data))
    
    return sha_1
#this function creates a commit object that references to a tree object and optionally a parent commit,
#on a given tree sha1, commit message and the identifier to a parent commit, it contructs the commit object,
#and writes it to the .pygit/objects directory, returning the sha1 hash of the commit object.
def commit_tree(tree_sha1, message, parent_sha1=None):
    lines  = [f'tree {tree_sha1}']

    if parent_sha1:
        lines.append(f'parent {parent_sha1}')

    timestamp = int(time.time())
    utc_offset = '+0000'
    author_info = f"Dev <dev@example.com> {timestamp} {utc_offset}"

    lines.append(f'author {author_info}')
    lines.append(f'committer {author_info}')

    lines.append("")
    lines.append(message)

    payload  = "\n".join(lines).encode("utf-8")
    header =  f"commit {len(payload)}\0".encode("utf-8")
    full_data = header + payload

    commit_sha1 = hashlib.sha1(full_data).hexdigest()

    dir_name = os.path.join(".pygit", "objects", commit_sha1[:2])
    dir_file = os.path.join(dir_name, commit_sha1[2:])
    os.makedirs(dir_name, exist_ok=True)
    if not os.path.exists(dir_file):
        with open(dir_file, "wb") as f:
            f.write(zlib.compress(full_data))
    return commit_sha1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pygit.py <command> [args]")
        sys.exit(1)

    command = sys.argv[1]
    if command == "init":
        init()
    elif command == "hash-object":
        file_path = sys.argv[2]
        sha1 = has_objects(file_path, write = True)
        print(sha1)
    elif command == "cat-file":
        sha1 = sys.argv[2]
        cat_file(sha1)

    elif command == "write-tree":
        sha_1 = write_tree(".") 
        print(sha_1)
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
    elif command == "commit-tree":
        tree_sha1 = sys.argv[2]
        message = sys.argv[3]
        parent_sha1 = sys.argv[4] if len(sys.argv) > 4 else None
        commit_sha1 = commit_tree(tree_sha1, message, parent_sha1)
        print(commit_sha1)
    elif command == "status":
        from pygit.status import status
        status()


