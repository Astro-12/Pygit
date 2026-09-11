# PyGit — Git Built from Scratch in Python

A lightweight, educational implementation of Git's core internal object database and version control mechanics written in pure Python.

`pygit` focuses on Git's **plumbing commands**—demonstrating how Git operates under the hood as a content-addressable key-value file system using SHA-1 hashing and zlib compression.

---

##  Features Implemented So Far

- **`init`**: Initializes a hidden `.pygit` directory with default branch refs (`refs/heads/main`) and an object database store (`.pygit/objects`).
- **`hash-object`**: Converts a single file into a Git **Blob** object, prepends binary header metadata (`blob <size>\0`), calculates its 40-character SHA-1 hash, and compresses it to disk via `zlib`.
- **`cat-file`**: Retrieves any stored object by its 40-character SHA-1 hash key, decompresses the payload, strips internal headers, and streams original contents to terminal `stdout`.
- **`write-tree`**: Recursively scans working directory folders to form **Tree** objects, mapping filenames and directory permissions directly to their corresponding binary SHA-1 Blob and sub-Tree hashes.

---

##  Architecture & Core Concepts

Git is essentially a key-value database built on top of your operating system's file system:
- **Keys:** 40-character cryptographic SHA-1 hashes (e.g., `557db03de997c86a4a...`).
- **Values:** `zlib`-compressed binary payloads formatted as `<type> <size>\0<content>`.
