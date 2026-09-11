import json
import os
import sys
import hashlib

INDEX_FILE = ".pygit/index"

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

def add_directory(directory: str = '.', hash_fn=None):
    #add all files in the given directory and its subdirectories to the index file
    #, creating blob objects for each file
    for root, dirs, files in os.walk(directory):
        if ".pygit" in dirs:
            dirs.remove(".pygit")  #skip .pygit directory
        for file in files:
            filepath = os.path.join(root, file)
            blob_sha1 = hash_fn(filepath, write=True)  #call main.py hash object
            add_to_index(filepath, blob_sha1)  #add file to index