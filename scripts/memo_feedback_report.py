"""메모로 쓰기 선택·수정 기록 요약: python scripts/memo_feedback_report.py"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

import memo_feedback  # noqa: E402

print(json.dumps(memo_feedback.summarize(memo_feedback.load_records()), ensure_ascii=False, indent=1))
