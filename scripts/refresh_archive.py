"""매일 과거 글 아카이브를 갱신한다(launchd com.dongpirang.archive)."""
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

import archive_refresh  # noqa: E402

try:
    result = archive_refresh.refresh()
except Exception as exc:  # noqa: BLE001
    result = {"error": repr(exc)}
print(datetime.now().isoformat(timespec="seconds"), result, flush=True)
sys.exit(1 if "error" in result else 0)
