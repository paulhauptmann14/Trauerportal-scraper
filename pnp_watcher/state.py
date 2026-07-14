import json
from pathlib import Path


class State:
    def __init__(self, path: Path, seen_ids: set[int], is_first_run: bool):
        self._path = path
        self._seen_ids = seen_ids
        self.is_first_run = is_first_run

    @classmethod
    def load(cls, path: Path) -> "State":
        path = Path(path)
        if not path.exists():
            return cls(path, seen_ids=set(), is_first_run=True)
        try:
            data = json.loads(path.read_text())
            seen_ids = set(data.get("seen_ids", []))
        except (json.JSONDecodeError, OSError):
            return cls(path, seen_ids=set(), is_first_run=True)
        return cls(path, seen_ids=seen_ids, is_first_run=False)

    def is_new(self, notice_id: int) -> bool:
        return notice_id not in self._seen_ids

    def mark_seen(self, notice_id: int) -> None:
        self._seen_ids.add(notice_id)

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps({"seen_ids": sorted(self._seen_ids)}))
