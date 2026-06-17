"""RAST 공개 문서의 링크와 해석 한계를 점검하는 CLI입니다."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rast.evaluation.docs_consistency import check_docs_consistency


def main() -> int:
    result = check_docs_consistency(ROOT)
    if result.passed:
        print("docs_consistency: PASS")
        return 0

    print("docs_consistency: FAIL")
    for failure in result.failures:
        print(f"- {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
