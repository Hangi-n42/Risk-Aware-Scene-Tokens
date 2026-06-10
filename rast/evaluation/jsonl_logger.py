"""Append-only JSONL logger입니다."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JSONLLogger:
    """실험 step record를 UTF-8 JSONL 파일에 append합니다."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(self, record: Any) -> None:
        """Pydantic 모델 또는 dict record를 한 줄 JSON으로 저장합니다."""

        payload = self._to_payload(record)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def read_all(self) -> list[dict[str, Any]]:
        """테스트와 간단한 검증을 위해 JSONL 전체를 읽습니다."""

        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    @staticmethod
    def _to_payload(record: Any) -> dict[str, Any]:
        if hasattr(record, "to_dict"):
            return record.to_dict()
        if hasattr(record, "model_dump"):
            return record.model_dump(mode="json", exclude_none=True)
        if isinstance(record, dict):
            return record
        raise TypeError(f"JSONL record로 저장할 수 없는 값입니다: {type(record)!r}")
