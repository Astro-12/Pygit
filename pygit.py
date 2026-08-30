import os
import sys
import hashlib
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

def write_tree():
    tree_entries = []

    # Iterate through the files in the current directory
    for item in sorted(os.listdir():

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
