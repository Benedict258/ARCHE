import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


class LocalVectorStore:
    """A tiny file-backed vector store fallback for demo/dev.

    This is NOT a production vector DB. It provides add() and query() methods
    so the memory layer can run without an external `chromadb` service.
    """

    def __init__(self, path: str = "data/local_vectors.json"):
        self.path = Path(path)
        self._data: Dict[str, Dict[str, Any]] = {}
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self._data = {}

    def add(self, key: str, vector: List[float], metadata: Dict[str, Any] | None = None):
        self._data[key] = {"vector": vector, "metadata": metadata or {}}
        self._persist()

    def query(self, vector: List[float], top_k: int = 10) -> List[Tuple[str, Dict[str, Any]]]:
        # naive retrieval: return most recent entries up to top_k
        items = list(self._data.items())
        return [(k, v.get("metadata", {})) for k, v in items[:top_k]]

    def _persist(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, ensure_ascii=False), encoding="utf-8")
