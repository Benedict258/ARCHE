import json
import math
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
        if not self._data:
            return []

        scored: list[tuple[float, str, Dict[str, Any]]] = []
        for key, payload in self._data.items():
            stored_vector = payload.get("vector") or []
            score = self._cosine_similarity(vector, stored_vector)
            scored.append((score, key, payload.get("metadata", {})))

        scored.sort(key=lambda item: (-item[0], item[1]))
        return [(key, metadata) for _, key, metadata in scored[:top_k]]

    @staticmethod
    def _cosine_similarity(left: List[float], right: List[float]) -> float:
        if not left or not right:
            return 0.0
        length = min(len(left), len(right))
        left_slice = left[:length]
        right_slice = right[:length]
        left_norm = math.sqrt(sum(value * value for value in left_slice))
        right_norm = math.sqrt(sum(value * value for value in right_slice))
        if not left_norm or not right_norm:
            return 0.0
        return sum(a * b for a, b in zip(left_slice, right_slice)) / (left_norm * right_norm)

    def _persist(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, ensure_ascii=False), encoding="utf-8")
