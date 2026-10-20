import json
import os
import sys
import hashlib

INDEX_FILE = ".git/index"

def read_index():
    #read index file, return list of entries
    if not os.path.exists(INDEX_FILE):
        return []
    with open(INDEX_FILE, "r") as f:
        return json.load(f)

def write_index(entries):
    #write list of entries to index file
    with open(INDEX_FILE, "w") as f:
        json.dump(entries, f, indent=4)

def add_to_index(file_path: str, blob_sha1: str):
    #add a new entry to the index file, with the given file path and blob SHA-1 hash
    entries = read_index()
    entries = [e for e in entries if e["path"] != file_path]  #remove old entry if it exists

    stat = os.stat(file_path)

    entries.append({
        "path": file_path,
        "sha1": blob_sha1,
        "mode": '100644' if os.path.isfile(file_path) else '40000',
        "size": stat.st_size,
        "mtime": stat.st_mtime
    })
    write_index(entries)

def add_directory(path: str = '.', hash_fn=None):
    # Add all files in the given path (file or directory) to the index
    if hash_fn is None:
        raise ValueError("hash_fn is required")
    
    if os.path.isfile(path):
        blob_sha1 = hash_fn(path, write=True)
        add_to_index(path, blob_sha1)
    else:
        for root, dirs, files in os.walk(path):
            if ".git" in dirs:
                dirs.remove(".git")
            for file in files:
                filepath = os.path.join(root, file)
                blob_sha1 = hash_fn(filepath, write=True)
                add_to_index(filepath, blob_sha1)