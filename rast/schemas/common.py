"""RAST 공통 schema primitive를 정의합니다."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field


SCHEMA_VERSION = "rast.v0.2"


class RASTBaseModel(BaseModel):
    """Pydantic v1/v2 차이를 감춘 공통 직렬화 기반 모델입니다."""

    def to_dict(self, *, exclude_none: bool = True) -> dict[str, Any]:
        """JSONL 기록에 바로 쓸 수 있는 dict로 변환합니다."""

        if hasattr(self, "model_dump"):
            return self.model_dump(mode="json", exclude_none=exclude_none)
        return self.dict(exclude_none=exclude_none)

    def to_json(self, *, exclude_none: bool = True) -> str:
        """한 줄 JSONL에 적합한 UTF-8 JSON 문자열로 변환합니다."""

        return json.dumps(self.to_dict(exclude_none=exclude_none), ensure_ascii=False)


class Vector3(RASTBaseModel):
    """3차원 위치, 크기, 속도, 회전 값을 표현합니다."""

    x: float = Field(description="X축 값입니다.")
    y: float = Field(description="Y축 값입니다.")
    z: float = Field(description="Z축 값입니다.")


class BBox2D(RASTBaseModel):
    """원본 이미지 영역을 가리키는 2D bounding box입니다."""

    x: float = Field(ge=0, description="좌상단 X 좌표입니다.")
    y: float = Field(ge=0, description="좌상단 Y 좌표입니다.")
    width: float = Field(ge=0, description="영역 너비입니다.")
    height: float = Field(ge=0, description="영역 높이입니다.")
