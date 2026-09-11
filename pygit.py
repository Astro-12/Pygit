import os
import sys
import hashlib
import time
import zlib

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

def write_tree(directory="."):
    tree_entries = []

    #repeatdely scans the whole script to find all the files in the current directory and its subdirectories, and adds them to the tree_entries list
    for item in sorted(os.listdir(directory)):
        if item.startswith(".pygit") or item.startswith(".git"):
            continue

        full_path = os.path.join(directory, item)

        if os.path.isfile(full_path):
            #forming blob
            sha1_hex = has_objects(full_path, write = True)
            sha1_bytes = bytes.fromhex(sha1_hex)
            
            mode = "100644"

            entry = f"{mode} {item}\0".encode("utf-8") + sha1_bytes
            tree_entries.append(entry)


        elif os.path.isdir(full_path):
            sha1_hex = write_tree(full_path)
            sha1_bytes = bytes.fromhex(sha1_hex)
            mode = "40000"

            entry = f"{mode} {item}\0".encode("utf-8") + sha1_bytes
            tree_entries.append(entry)

    #assembles the tree object by concatenating the entries and creating a header for the tree object, then compresses and writes it to the .pygit/objects directory
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
