import os
import sys

def init():
    os.makedirs(".pygit/objects", exist_ok=True)
    os.makedirs(".pygit/refs/heads", exist_ok=True)
        
    with open(".pygit/HEAD", "w") as f:
        f.write("ref: refs/heads/main\n")
        
    print("Initialized empty PyGit repository in .pygit/")

if __name__ == "__main__":
    if sys.argv[1] == "init":
        init()
