

import hashlib
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from collections import deque


# =========================
# Commit Object
# =========================
class Commit:
    def __init__(self, message: str, author: str, parent: Optional[str] = None):
        self.id = self._generate_id()
        self.message = message
        self.author = author
        self.timestamp = datetime.now().isoformat()
        self.parent = parent
        self.files: Dict[str, str] = {}
        self.children: List[str] = []

    def _generate_id(self) -> str:
        raw = f"{datetime.now().isoformat()}{os.urandom(16).hex()}"
        return hashlib.sha1(raw.encode()).hexdigest()[:8]

    def add_file(self, filepath: str, file_hash: str):
        self.files[filepath] = file_hash

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "message": self.message,
            "author": self.author,
            "timestamp": self.timestamp,
            "parent": self.parent,
            "files": self.files,
            "children": self.children,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Commit":
        obj = cls.__new__(cls)
        obj.id = data["id"]
        obj.message = data["message"]
        obj.author = data["author"]
        obj.timestamp = data["timestamp"]
        obj.parent = data["parent"]
        obj.files = data["files"]
        obj.children = data["children"]
        return obj


# =========================
# Commit Graph
# =========================
class CommitGraph:
    def __init__(self):
        self.commits: Dict[str, Commit] = {}
        self.head: Optional[str] = None
        self.branches: Dict[str, Optional[str]] = {"main": None}
        self.current_branch = "main"

    def add_commit(self, commit: Commit) -> str:
        self.commits[commit.id] = commit

        if commit.parent and commit.parent in self.commits:
            self.commits[commit.parent].children.append(commit.id)

        self.head = commit.id
        self.branches[self.current_branch] = commit.id
        return commit.id

    def get_commit(self, commit_id: str) -> Optional[Commit]:
        return self.commits.get(commit_id)

    def get_history(self, start: Optional[str] = None) -> List[Commit]:
        history = []
        current = start or self.head

        while current:
            commit = self.commits.get(current)
            if not commit:
                break
            history.append(commit)
            current = commit.parent

        return history

    def create_branch(self, name: str):
        self.branches[name] = self.head

    def checkout_branch(self, name: str) -> bool:
        if name not in self.branches:
            return False
        self.current_branch = name
        self.head = self.branches[name]
        return True


# =========================
# File Store (NO SIDE EFFECTS)
# =========================
class FileStore:
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.objects_dir = repo_path / ".aivcs" / "objects"

    def ensure(self):
        self.objects_dir.mkdir(parents=True, exist_ok=True)

    def hash_file(self, filepath: Path) -> str:
        sha1 = hashlib.sha1()
        with open(filepath, "rb") as f:
            while chunk := f.read(8192):
                sha1.update(chunk)
        return sha1.hexdigest()

    def store_file(self, filepath: Path) -> str:
        self.ensure()
        file_hash = self.hash_file(filepath)
        obj_dir = self.objects_dir / file_hash[:2]
        obj_dir.mkdir(exist_ok=True)
        obj_path = obj_dir / file_hash[2:]

        if not obj_path.exists():
            shutil.copy2(filepath, obj_path)

        return file_hash

    def restore_file(self, file_hash: str, target: Path):
        obj_path = self.objects_dir / file_hash[:2] / file_hash[2:]
        if obj_path.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(obj_path, target)


# =========================
# Staging Area
# =========================
class StagingArea:
    def __init__(self):
        self.staged_files: Set[str] = set()
        self.file_hashes: Dict[str, str] = {}

    def add(self, path: str, file_hash: str):
        self.staged_files.add(path)
        self.file_hashes[path] = file_hash

    def clear(self):
        self.staged_files.clear()
        self.file_hashes.clear()

    def is_empty(self) -> bool:
        return not self.staged_files

    def get_files(self) -> Dict[str, str]:
        return dict(self.file_hashes)


# =========================
# History Stack
# =========================
class HistoryStack:
    def __init__(self, maxsize=100):
        self.stack = deque(maxlen=maxsize)

    def push(self, commit_id: str):
        self.stack.append(commit_id)

    def pop(self) -> Optional[str]:
        return self.stack.pop() if self.stack else None

    def peek(self) -> Optional[str]:
        return self.stack[-1] if self.stack else None

    def size(self) -> int:
        return len(self.stack)


# =========================
# MAIN VCS CLASS (PATCHED)
# =========================
class AIVersionControl:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        self.vcs_dir = self.repo_path / ".aivcs"

        self.graph = CommitGraph()
        self.staging = StagingArea()
        self.history = HistoryStack()
        self.file_store: Optional[FileStore] = None

        self.config = {"author": "User"}

    # ---------- INIT ----------
    def init(self) -> bool:
        if self.vcs_dir.exists():
            return False

        self.vcs_dir.mkdir()
        (self.vcs_dir / "objects").mkdir()
        (self.vcs_dir / "refs").mkdir()

        self.file_store = FileStore(self.repo_path)
        self._save_state()
        return True

    # ---------- LOAD ----------
    @classmethod
    def load(cls, repo_path: str) -> Optional["AIVersionControl"]:
        vcs = cls(repo_path)
        if not vcs.vcs_dir.exists():
            return None

        if vcs._load_state():
            vcs.file_store = FileStore(vcs.repo_path)
            return vcs

        return None

    # ---------- ADD ----------
    def add(self, filepath: str) -> bool:
        if not self.file_store:
            return False

        file_path = self.repo_path / filepath
        if not file_path.exists() or not file_path.is_file():
            return False

        file_hash = self.file_store.store_file(file_path)
        self.staging.add(filepath, file_hash)
        return True

    # ---------- COMMIT ----------
    def commit(self, message: str, author: Optional[str] = None) -> Optional[str]:
        if self.staging.is_empty():
            return None

        commit = Commit(
            message=message,
            author=author or self.config["author"],
            parent=self.graph.head,
        )

        for path, h in self.staging.get_files().items():
            commit.add_file(path, h)

        cid = self.graph.add_commit(commit)
        self.history.push(cid)
        self.staging.clear()
        self._save_state()
        return cid

    # ---------- LOG ----------
    def log(self, limit=10) -> List[Dict]:
        return [c.to_dict() for c in self.graph.get_history()[:limit]]

    # ---------- STATUS ----------
    def status(self) -> Dict:
        return {
            "branch": self.graph.current_branch,
            "head": self.graph.head,
            "staged_files": list(self.staging.staged_files),
            "total_commits": len(self.graph.commits),
        }

    # ---------- BRANCH ----------
    def create_branch(self, name: str) -> bool:
        if name in self.graph.branches:
            return False
        self.graph.create_branch(name)
        self._save_state()
        return True

    def switch_branch(self, name: str) -> bool:
        if not self.graph.checkout_branch(name):
            return False
        self._save_state()
        return True
    
    def branches(self) -> List[str]:
        return list(self.graph.branches.keys())


    # ---------- CHECKOUT ----------
    def checkout(self, commit_id: str) -> bool:
        commit = self.graph.get_commit(commit_id)
        if not commit or not self.file_store:
            return False

        for path, h in commit.files.items():
            self.file_store.restore_file(h, self.repo_path / path)

        self.graph.head = commit_id
        self._save_state()
        return True

    # ---------- STATE ----------
    def _save_state(self):
        state = {
            "graph": {
                "commits": {k: v.to_dict() for k, v in self.graph.commits.items()},
                "head": self.graph.head,
                "branches": self.graph.branches,
                "current_branch": self.graph.current_branch,
            },
            "config": self.config,
        }
        with open(self.vcs_dir / "state.json", "w") as f:
            json.dump(state, f, indent=2)

    def _load_state(self) -> bool:
        state_file = self.vcs_dir / "state.json"
        if not state_file.exists():
            return False

        with open(state_file) as f:
            state = json.load(f)

        self.graph.commits = {
            k: Commit.from_dict(v) for k, v in state["graph"]["commits"].items()
        }
        self.graph.head = state["graph"]["head"]
        self.graph.branches = state["graph"]["branches"]
        self.graph.current_branch = state["graph"]["current_branch"]
        self.config = state.get("config", {"author": "User"})

        for c in self.graph.get_history():
            self.history.push(c.id)

        return True
