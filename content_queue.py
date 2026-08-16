"""발행 큐 저장소.

앱(발행 큐 탭)과 배치 스크립트(초안 생성·발행 워커)가 공유하는
로컬 JSON 파일 기반 큐. 스키마:

{
  "materials": [{"id", "text", "created_at", "used"}],
  "drafts": [{"id", "text", "pillar", "status", "slot",
               "image_prompt", "material_id", "created_at",
               # 아래는 전부 선택 필드 — 과거 기록엔 없을 수 있으니
               # 항상 .get() 으로 읽는다 (load_queue 는 이 필드들을
               # setdefault 하지 않는다)
               "origin", "source_job_id", "source_kind", "updated_at",
               "manual_published", "published_at",
               # publish_worker.py 가 API 발행 시에만 쓰는 필드
               "tweet_id"}],
  "settings": {"tip_keywords"},              # 사용자가 손으로 고치는 값
  "reminders": {"stale_drafts_at"}           # 배치가 쓰는 운영 상태
}

status 는 여섯 가지다.
  - draft: 아직 승인 전. 자유롭게 고칠 수 있는(editable) 유일한 상태
  - approved: 슬롯이 배정되어 발행을 기다림
  - publishing: scripts/publish_worker.py 가 발행을 시도 중이라고 찜한
    상태 — 워커가 중간에 죽으면 다음 실행이 이 상태를 발견해 error 로
    돌린다(실제로 발행됐는지 알 수 없어서다)
  - error: 발행 시도가 실패했거나 publishing 에서 회수됨. 사람 확인 필요
  - published: 발행 완료. tweet_id 가 있으면 API로 발행된 것이고,
    manual_published 가 True 면 사람이 수동으로 올리고 표시만 한 것 —
    이 두 경우는 절대 동시에 만들어지지 않는다
  - rejected: 반려됨
(publishing/error/tweet_id/published_at 은 scripts/publish_worker.py 가
쓰는 필드이며 publisher.py 는 건드리지 않는다.)

slot: 승인 시 배정되는 발행 예정 시각 (ISO 문자열, 로컬 시간).
mark_manual_published 로 수동 발행 표시를 하면 슬롯은 다시 None 이 된다.

워크스페이스(NiceGUI) 전용 선택 필드:
  - origin: "workspace" 면 upsert_workspace_draft 로 새로 만든 초안
  - source_job_id / source_kind: 초안이 나온 워크스페이스·아이디어 작업의
    id/kind (idea_jobs.py, workspace_jobs.py 의 job 레코드를 가리킨다).
    예외 하나: source_kind="reuse"(workspace_ui.publish 의 히스토리 재사용)
    일 때는 진짜 작업이 없으므로 source_job_id 가 "publish-reuse:{원본 초안
    id}" 형태의 합성 값이다 — job 레코드를 가리키지 않고, 이 초안이 어떤
    과거 초안에서 복제됐는지만 남긴다.
  - updated_at: 워크스페이스 자동저장이 마지막으로 고친 시각
  - manual_published: True 면 API 없이 사람이 직접 올리고 표시만 한 것
  - published_at: 발행 완료 시각 (API 발행·수동 발행 공통)

settings/reminders 는 선택적이다. reminders 는 scripts/generate_drafts.py 가
승인 대기 리마인드를 중복 발송하지 않으려고 기록하는 값이라 사람이 만질
필요가 없다 — 사용자 설정(settings)과 섞지 않으려고 따로 뒀다.
"""

from __future__ import annotations

import fcntl
import json
import os
import tempfile
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

QUEUE_PATH = Path("content_queue/queue.json")

# 발행 슬롯: 평일 08시·19시, 토요일 10시, 일요일 없음 (스케줄러 탭의
# 한국 시간대 피크 지식을 그대로 반영)
_WEEKDAY_SLOTS = {
    0: (8, 19),   # 월
    1: (8, 19),   # 화
    2: (8, 19),   # 수
    3: (8, 19),   # 목
    4: (8, 19),   # 금
    5: (10,),     # 토
    6: (),        # 일
}

PILLARS = ("build_in_public", "retrospective", "tip", "curation")


def empty_queue() -> dict:
    return {"materials": [], "drafts": []}


def load_queue(path: Path = QUEUE_PATH) -> dict:
    path = Path(path)
    if not path.is_file():
        return empty_queue()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return empty_queue()
    if not isinstance(data, dict):
        return empty_queue()
    data.setdefault("materials", [])
    data.setdefault("drafts", [])
    return data


def save_queue(path: Path, data: dict) -> None:
    """큐를 원자적으로 저장한다.

    같은 디렉터리에 매번 고유한 이름의 임시 파일을 만들어 쓴 뒤
    os.replace 로 교체한다. 고정된 이름(.tmp)을 쓰면 앱과 배치 스크립트가
    동시에 저장할 때 서로의 임시 파일을 덮어써 둘 중 하나가 깨진 채로
    끝날 수 있다 — 각 쓰기가 자기만의 tmp 를 갖게 해서 이를 막는다.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=2))
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


@contextmanager
def queue_lock(path: Path = QUEUE_PATH, timeout: float = 10.0):
    """큐 파일 락 — load-mutate-save 트랜잭션 전체를 감싼다.

    앱(Streamlit)과 launchd 배치(generate_drafts, publish_worker)가 같은
    queue.json 을 읽고-수정-쓰기 때문에, 락 없이는 나중에 저장하는 쪽이
    상대의 변경을 조용히 되돌린다. flock 은 프로세스가 죽으면 자동
    해제되므로 스테일 락 걱정이 없다. 타임아웃 시 TimeoutError.
    """
    lock_path = Path(path).with_suffix(".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "w") as lf:
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(lf, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        f"queue lock timeout ({timeout}s): {lock_path}"
                    )
                time.sleep(0.05)
        try:
            yield
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


@contextmanager
def queue_transaction(path: Path = QUEUE_PATH, timeout: float = 10.0):
    """락 아래에서 큐를 읽고, 블록이 정상 종료하면 저장한다.

    예외가 나면 저장하지 않는다 — 부분 변경이 파일에 남지 않는다.
    """
    with queue_lock(path, timeout=timeout):
        data = load_queue(path)
        yield data
        save_queue(path, data)


def next_slots(after: datetime, count: int) -> list[datetime]:
    """after 이후의 발행 슬롯을 시간순으로 count 개 돌려준다."""
    slots: list[datetime] = []
    day = after.replace(hour=0, minute=0, second=0, microsecond=0)
    while len(slots) < count:
        for hour in _WEEKDAY_SLOTS[day.weekday()]:
            slot = day.replace(hour=hour)
            if slot > after:
                slots.append(slot)
                if len(slots) == count:
                    break
        day += timedelta(days=1)
    return slots


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def add_material(data: dict, text: str) -> dict | None:
    text = (text or "").strip()
    if not text:
        return None
    material = {
        "id": _new_id(),
        "text": text,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "used": False,
    }
    data["materials"].append(material)
    return material


def unused_materials(data: dict) -> list[dict]:
    return [m for m in data["materials"] if not m.get("used")]


def remove_material(data: dict, material_id: str) -> None:
    data["materials"] = [m for m in data["materials"] if m["id"] != material_id]


def add_draft(
    data: dict,
    *,
    text: str,
    pillar: str,
    image_prompt: str = "",
    material_id: str | None = None,
) -> dict:
    draft = {
        "id": _new_id(),
        "text": text,
        "pillar": pillar,
        "status": "draft",
        "slot": None,
        "image_prompt": image_prompt,
        "material_id": material_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    data["drafts"].append(draft)
    if material_id:
        for m in data["materials"]:
            if m["id"] == material_id:
                m["used"] = True
    return draft


def _find_draft(data: dict, draft_id: str) -> dict | None:
    for d in data["drafts"]:
        if d["id"] == draft_id:
            return d
    return None


def approve_draft(data: dict, draft_id: str, now: datetime | None = None) -> dict | None:
    """초안을 승인하고 아직 배정되지 않은 가장 이른 슬롯을 배정한다."""
    draft = _find_draft(data, draft_id)
    if draft is None:
        return None
    now = now or datetime.now()
    taken = {
        d["slot"]
        for d in data["drafts"]
        if d.get("slot") and d["status"] in ("approved", "published")
    }
    for slot in next_slots(now, count=len(taken) + 1):
        iso = slot.isoformat()
        if iso not in taken:
            draft["slot"] = iso
            break
    draft["status"] = "approved"
    return draft


def reject_draft(data: dict, draft_id: str) -> None:
    draft = _find_draft(data, draft_id)
    if draft:
        draft["status"] = "rejected"
        draft["slot"] = None


def update_draft_text(data: dict, draft_id: str, text: str) -> None:
    draft = _find_draft(data, draft_id)
    if draft:
        draft["text"] = text


def remove_draft(data: dict, draft_id: str) -> None:
    data["drafts"] = [d for d in data["drafts"] if d["id"] != draft_id]


def get_draft(data: dict, draft_id: str) -> dict | None:
    """draft_id 로 초안을 찾는다. 없으면 None."""
    return _find_draft(data, draft_id)


def upsert_workspace_draft(
    data: dict,
    draft_id: str | None,
    text: str,
    pillar: str,
    source_job_id: str | None = None,
    source_kind: str | None = None,
) -> dict | None:
    """워크스페이스 자동저장.

    반환 계약 — None 은 "본문이 비어 있다" 는 경우에만 나온다:
      - 본문이 공백뿐이면 아무것도 만들거나 바꾸지 않고 None.
      - draft_id 가 None 이면 새 초안을 만들어 돌려준다.
      - draft_id 가 있고 그 초안이 아직 "draft" 상태면 그 초안을 제자리에서
        갱신해 돌려준다.
      - draft_id 가 있지만 그 초안이 없거나(오탈자·삭제됨) 이미 승인/발행/
        반려 등 편집 불가 상태라면, 그 옛 레코드는 절대 건드리지 않고
        대신 새 초안을 만들어 돌려준다. 사람이 입력한 본문을 조용히
        버리지 않기 위해서다 — 에디터 자동저장은 무손실이어야 한다.
        원본 초안이 승인/발행된 뒤에 들어온 편집은 사라지는 대신 새
        초안이 된다.

    갱신 경로에서 source_job_id/source_kind 를 생략(None)하면 기존 값이
    그대로 유지된다 — 자동저장 호출마다 provenance 를 다시 보내지 않아도
    널로 덮어써지지 않는다. 값을 실제로 지우고 싶다면 이 함수가 아니라
    직접 초안을 고쳐야 한다.

    이 함수는 data 를 직접 바꿀 뿐 저장하지 않는다 — 호출자의
    queue_transaction 블록 안에서 get_draft 와 조합해 원자적으로 쓰도록
    설계됐다.
    """
    text = (text or "").strip()
    if not text:
        return None

    now_iso = datetime.now().isoformat(timespec="seconds")

    draft = _find_draft(data, draft_id) if draft_id is not None else None
    if draft is not None and draft.get("status") == "draft":
        draft["text"] = text
        draft["pillar"] = pillar
        if source_job_id is not None:
            draft["source_job_id"] = source_job_id
        if source_kind is not None:
            draft["source_kind"] = source_kind
        draft["updated_at"] = now_iso
        return draft

    # draft_id 가 None 이거나, 가리키는 초안이 없거나, 더는 편집 가능한
    # 상태가 아니다 — 옛 레코드는 그대로 두고 새 초안을 만든다.
    new_draft = {
        "id": _new_id(),
        "text": text,
        "pillar": pillar,
        "status": "draft",
        "slot": None,
        "image_prompt": "",
        "material_id": None,
        "created_at": now_iso,
        "origin": "workspace",
        "source_job_id": source_job_id,
        "source_kind": source_kind,
        "updated_at": now_iso,
    }
    data["drafts"].append(new_draft)
    return new_draft


def mark_manual_published(
    data: dict, draft_id: str, now: datetime | None = None
) -> dict | None:
    """API 없이 사람이 직접 올린 글을 발행 완료로 표시한다.

    tweet_id 는 절대 만들어내지 않는다 — tweet_id 유무가 API 발행과
    수동 발행을 구분하는 유일한 표식이기 때문이다. 이미 tweet_id 가
    있는 초안(=API로 발행됨)은 건드리지 않고 None 을 돌려준다 — 한
    초안이 API 발행과 수동 발행 두 가지로 동시에 표시되는 일은 없어야
    한다.
    """
    draft = _find_draft(data, draft_id)
    if draft is None:
        return None
    if draft.get("tweet_id"):
        return None
    now = now or datetime.now()
    draft["status"] = "published"
    draft["manual_published"] = True
    draft["published_at"] = now.isoformat(timespec="seconds")
    draft["slot"] = None
    return draft


def duplicate_draft(data: dict, draft_id: str) -> dict | None:
    """히스토리(발행됐거나 반려된 글 포함)를 새 편집 가능한 초안으로
    복제한다.

    원본은 절대 건드리지 않는다. 새-초안 생성 경로(upsert_workspace_draft)를
    그대로 타므로, text/pillar 만 옮겨지고 image_prompt·material_id·
    tweet_id 같은 발행 당시 맥락은 새 초안에 들고 오지 않는다.
    """
    source = _find_draft(data, draft_id)
    if source is None:
        return None
    return upsert_workspace_draft(
        data,
        draft_id=None,
        text=source.get("text", ""),
        pillar=source.get("pillar"),
    )


def drafts_for_statuses(data: dict, statuses: set[str]) -> list[dict]:
    """주어진 상태 집합에 속하는 초안만 순서대로 돌려준다.

    "published" 를 넣으면 API로 발행된 글(tweet_id 있음)과 사람이 수동으로
    표시한 글(manual_published)이 구분 없이 함께 나온다 — 상태값 자체가
    이미 둘을 하나로 묶어서 나타내기 때문에 따로 분기할 필요가 없다.
    """
    return [d for d in data["drafts"] if d.get("status") in statuses]
