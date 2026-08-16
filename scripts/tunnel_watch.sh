#!/bin/bash
# Tailscale Serve 워처 — launchd가 1시간마다 호출.
#
# 동작:
# 1. 로컬 앱 두 개가 죽어 있으면 살린다.
#      NiceGUI 워크스페이스 :8080  (주 진입점)
#      레거시 Streamlit    :8501  (기존 도구 모음)
# 2. Tailscale Serve 로 테일넷 안에서만 열어둔다.
#      https :10000 -> 127.0.0.1:8080
#      https :10001 -> 127.0.0.1:8501
# 3. URL이 바뀌었을 때만(사실상 최초 1회) 관리자에게 텔레그램 발송.
#
# Funnel(공개 노출)은 더 쓰지 않는다. 접근 통제를 테일넷으로 옮겼기 때문에
# 앱 안의 접속 게이트도 함께 없앴다.
#
# 절대 금지: tailscale serve / funnel 의 reset 하위 명령.
# 이 노드는 :443 -> 8790, :8443 -> ai-trader(8502) 도 함께 서빙하는데
# reset 은 포트를 가리지 않고 전부 지운다. 포트 단위 명령만 쓴다.
# tests/test_tailscale_serve_watch.py 가 그 형태가 없는지 검사한다.
#
# 수동 실행: bash scripts/tunnel_watch.sh
set -u

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$REPO/logs"
WORKSPACE_URL_FILE="$LOG_DIR/workspace.url"
LEGACY_URL_FILE="$LOG_DIR/legacy.url"
WATCH_LOG="$LOG_DIR/tunnel-watch.log"
NICEGUI_PORT=8080
LEGACY_APP_PORT=8501   # 주의: 8502는 ai-trader 대시보드가 사용 중
WORKSPACE_PORT=10000
LEGACY_PORT=10001
TS_BIN="/opt/homebrew/bin/tailscale"
PYTHON="$REPO/venv/bin/python"
# launchd는 최소 PATH(/usr/bin:/bin:/usr/sbin:/sbin)만 물려줘서
# CLI 프로바이더가 shutil.which()로 실행 파일을 못 찾는다.
# 설치 위치가 CLI와 그 런타임마다 다르므로 전부 넣는다:
#   claude, codex -> ~/.npm-global/bin
#   grok          -> ~/.local/bin (심볼릭 링크) / ~/.grok/bin (실제 위치)
#   node          -> /usr/local/bin (현재 설치) /opt/homebrew/bin (Homebrew 기본)
# 새 CLI 프로바이더를 추가하면 여기도 같이 갱신할 것.
# tests/test_tunnel_path.py 가 이 줄과 프로바이더 command 목록의 정합성을 검사한다.
export PATH="$HOME/.npm-global/bin:$HOME/.local/bin:$HOME/.grok/bin:/usr/local/bin:/opt/homebrew/bin:$PATH"

mkdir -p "$LOG_DIR"

log() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$WATCH_LOG"
}

# 00:00–06:59 KST 수면 시간대는 체크하지 않는다 (ai-trader와 동일 정책).
HOUR_NOW=$(date '+%H')
if (( 10#$HOUR_NOW < 7 )); then
    log "skip — sleep window (hour=$HOUR_NOW)"
    exit 0
fi

workspace_alive() {
    curl -sf -o /dev/null --max-time 5 "http://127.0.0.1:$NICEGUI_PORT/"
}

legacy_alive() {
    curl -sf -o /dev/null --max-time 5 "http://localhost:$LEGACY_APP_PORT"
}

ensure_nicegui() {
    if workspace_alive; then
        return 0
    fi
    log "workspace down — starting nicegui on :$NICEGUI_PORT"
    ( cd "$REPO" && NICEGUI_PORT="$NICEGUI_PORT" nohup "$PYTHON" nicegui_app.py \
        >> "$LOG_DIR/nicegui.log" 2>&1 & )
    local deadline=$((SECONDS + 45))
    while (( SECONDS < deadline )); do
        workspace_alive && { log "nicegui started"; return 0; }
        sleep 3
    done
    log "ERROR: nicegui failed to start in 45s"
    return 1
}

ensure_legacy_app() {
    if legacy_alive; then
        return 0
    fi
    log "legacy app down — starting streamlit on :$LEGACY_APP_PORT"
    ( cd "$REPO" && nohup "$PYTHON" -m streamlit run app.py \
        --server.headless true --server.port "$LEGACY_APP_PORT" \
        >> "$LOG_DIR/streamlit.log" 2>&1 & )
    local deadline=$((SECONDS + 45))
    while (( SECONDS < deadline )); do
        legacy_alive && { log "streamlit started"; return 0; }
        sleep 3
    done
    log "ERROR: streamlit failed to start in 45s"
    return 1
}

# serve status 의 AllowFunnel 블록만 떼어내 해당 포트가 공개인지 본다.
# jq 없이 파싱한다 (launchd 환경에 jq가 있다고 보장할 수 없다).
#
# AllowFunnel 키 자체가 안 보이면 두 가지다: (a) 공개된 포트가 하나도 없다,
# (b) 출력 모양이 바뀌어 파서가 헛돌고 있다. (b) 라면 이 함수는 "비공개"로
# 답하며 조용히 실패하고, 노출된 포트를 못 끄게 된다. 구분이 안 되니 최소한
# 로그는 남긴다 — Task 10 검증에서 :443/:8443 이 공개인 걸 이미 알기 때문에
# 이 줄이 뜨면 파서가 깨진 것으로 봐야 한다.
workspace_port_is_public() {
    local status_json
    status_json=$("$TS_BIN" serve status --json 2>/dev/null)
    if ! printf '%s' "$status_json" | grep -q '"AllowFunnel"'; then
        log "WARN: serve status --json has no AllowFunnel block — funnel probe may be blind"
        return 1
    fi
    printf '%s' "$status_json" | awk '
        /"AllowFunnel"[[:space:]]*:/ { inblock = 1; next }
        inblock && /^[[:space:]]*}/  { inblock = 0 }
        inblock                      { print }
    ' | grep -q ":$WORKSPACE_PORT\"[[:space:]]*:[[:space:]]*true"
}

# 사설 전환 전에 남아 있는 공개(Funnel) 설정을 딱 한 번 내린다.
# 가드가 중요하다: `funnel --https=PORT off` 는 그 포트의 웹 핸들러까지 같이
# 지우기 때문에, 무조건 실행하면 매시간 serve 설정이 날아가 접속이 끊긴다.
disable_workspace_funnel() {
    if workspace_port_is_public; then
        log "funnel still public on :$WORKSPACE_PORT — turning it off (tailnet only)"
        "$TS_BIN" funnel --https="$WORKSPACE_PORT" off >> "$WATCH_LOG" 2>&1 \
            || log "WARN: funnel off failed (:$WORKSPACE_PORT)"
    fi
}

# serve 로 붙은 https 엔드포인트의 URL을 찾는다. 호스트명은 하드코딩하지 않는다.
# 1순위 `serve status` 텍스트, 2순위 `serve status --json` 의 Web/AllowFunnel 키.
serve_url() {
    local port="$1" url hostport
    url=$("$TS_BIN" serve status 2>/dev/null \
        | grep -Eo "https://[A-Za-z0-9.-]+\.ts\.net:$port" | head -1)
    if [[ -z "$url" ]]; then
        hostport=$("$TS_BIN" serve status --json 2>/dev/null \
            | grep -Eo "\"[A-Za-z0-9.-]+\.ts\.net:$port\"" | head -1 | tr -d '"')
        [[ -n "$hostport" ]] && url="https://$hostport"
    fi
    printf '%s\n' "$url"
}

# serve 설정은 선언형이라 매번 같은 값으로 다시 걸어도 안전하다(멱등).
# 대상 포트가 바뀐 경우에도 이 방식이라야 실제로 교정된다.
ensure_workspace_serve() {
    "$TS_BIN" serve --bg --https="$WORKSPACE_PORT" "http://127.0.0.1:$NICEGUI_PORT" \
        >> "$WATCH_LOG" 2>&1 \
        || log "WARN: serve config failed (:$WORKSPACE_PORT -> $NICEGUI_PORT)"
}

ensure_legacy_serve() {
    "$TS_BIN" serve --bg --https="$LEGACY_PORT" "http://127.0.0.1:$LEGACY_APP_PORT" \
        >> "$WATCH_LOG" 2>&1 \
        || log "WARN: serve config failed (:$LEGACY_PORT -> $LEGACY_APP_PORT)"
}

STATUS=0
ensure_nicegui || STATUS=1
ensure_legacy_app || STATUS=1

disable_workspace_funnel
ensure_workspace_serve
ensure_legacy_serve
sleep 2

WORKSPACE_URL=$(serve_url "$WORKSPACE_PORT")
LEGACY_URL=$(serve_url "$LEGACY_PORT")

if [[ -z "$WORKSPACE_URL" || -z "$LEGACY_URL" ]]; then
    log "ERROR: serve endpoints not resolved (workspace='$WORKSPACE_URL' legacy='$LEGACY_URL')"
    exit 1
fi

for url in "$WORKSPACE_URL" "$LEGACY_URL"; do
    if ! curl -sf -o /dev/null --max-time 15 "$url/"; then
        # 테일넷 DNS 전파 지연이나 일시적 네트워크 문제일 수 있어 경고만 남긴다.
        log "WARN: serve URL not reachable right now ($url)"
    fi
done

LAST_WORKSPACE_URL=""
[[ -f "$WORKSPACE_URL_FILE" ]] && LAST_WORKSPACE_URL=$(head -n1 "$WORKSPACE_URL_FILE" 2>/dev/null | tr -d '[:space:]')
LAST_LEGACY_URL=""
[[ -f "$LEGACY_URL_FILE" ]] && LAST_LEGACY_URL=$(head -n1 "$LEGACY_URL_FILE" 2>/dev/null | tr -d '[:space:]')

if [[ "$WORKSPACE_URL" != "$LAST_WORKSPACE_URL" || "$LEGACY_URL" != "$LAST_LEGACY_URL" ]]; then
    printf '%s\n' "$WORKSPACE_URL" > "$WORKSPACE_URL_FILE"
    printf '%s\n' "$LEGACY_URL" > "$LEGACY_URL_FILE"
    MSG=$(printf '🐾 동피랑 접속 주소 (Tailscale 사설망)\n워크스페이스: %s\n레거시 도구: %s\n\n테일넷에 붙은 기기에서만 열린다. 재시작해도 주소는 그대로다.' \
        "$WORKSPACE_URL" "$LEGACY_URL")
    if "$PYTHON" "$REPO/scripts/notify_admin.py" "$MSG" >> "$WATCH_LOG" 2>&1; then
        log "admin notified (workspace=$WORKSPACE_URL legacy=$LEGACY_URL)"
    else
        log "telegram notify failed (continuing)"
    fi
fi

if (( STATUS == 0 )); then
    log "OK workspace=$WORKSPACE_URL legacy=$LEGACY_URL"
else
    log "DEGRADED workspace=$WORKSPACE_URL legacy=$LEGACY_URL (local app start failed)"
fi
exit $STATUS
