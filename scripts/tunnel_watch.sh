#!/bin/bash
# Tailscale Funnel 워처 — launchd가 1시간마다 호출.
#
# 동작:
# 1. 로컬 앱(8501)이 죽어 있으면 streamlit부터 살린다.
# 2. Tailscale Funnel(https :10000 → localhost:8501)이 꺼져 있으면 다시 켠다.
# 3. URL이 바뀌었을 때만(사실상 최초 1회) 관리자에게 텔레그램 발송.
#
# cloudflared Quick Tunnel은 재시작마다 URL이 바뀌어서, 고정 URL을 주는
# Tailscale Funnel로 교체했다. Funnel 사용 가능 포트(443/8443/10000) 중
# 443은 다른 서비스, 8443은 ai-trader(8502)가 쓰므로 이 앱은 10000을 쓴다.
#
# 수동 실행: bash scripts/tunnel_watch.sh
set -u

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$REPO/logs"
URL_FILE="$LOG_DIR/funnel.url"
WATCH_LOG="$LOG_DIR/tunnel-watch.log"
PORT=8501        # 주의: 8502는 ai-trader 대시보드가 사용 중
FUNNEL_PORT=10000
TS_BIN="/opt/homebrew/bin/tailscale"
PYTHON="$REPO/venv/bin/python"
# launchd는 최소 PATH(/usr/bin:/bin:/usr/sbin:/sbin)만 물려줘서
# ~/.npm-global/bin의 claude/codex CLI를 shutil.which()가 못 찾는다.
export PATH="$HOME/.npm-global/bin:$PATH"

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

app_alive() {
    curl -sf -o /dev/null --max-time 5 "http://localhost:$PORT"
}

ensure_app() {
    if app_alive; then
        return 0
    fi
    log "app down — starting streamlit on :$PORT"
    ( cd "$REPO" && nohup "$PYTHON" -m streamlit run app.py \
        --server.headless true --server.port "$PORT" \
        >> "$LOG_DIR/streamlit.log" 2>&1 & )
    local deadline=$((SECONDS + 45))
    while (( SECONDS < deadline )); do
        app_alive && { log "streamlit started"; return 0; }
        sleep 3
    done
    log "ERROR: streamlit failed to start in 45s"
    return 1
}

funnel_url() {
    "$TS_BIN" funnel status 2>/dev/null \
        | grep -Eo "https://[A-Za-z0-9.-]+\.ts\.net:$FUNNEL_PORT" | head -1
}

ensure_funnel() {
    local url
    url=$(funnel_url)
    if [[ -z "$url" ]]; then
        log "funnel off — enabling https=:$FUNNEL_PORT -> localhost:$PORT"
        "$TS_BIN" funnel --bg --https="$FUNNEL_PORT" "http://127.0.0.1:$PORT" \
            >> "$WATCH_LOG" 2>&1
        sleep 2
        url=$(funnel_url)
    fi
    if [[ -z "$url" ]]; then
        log "ERROR: tailscale funnel enable failed"
        return 1
    fi
    printf '%s\n' "$url"
}

ensure_app || exit 1
URL=$(ensure_funnel) || exit 1

if ! curl -sf -o /dev/null --max-time 15 "$URL/"; then
    # Funnel 엣지 전파 지연이나 일시적 네트워크 문제일 수 있어 경고만 남긴다.
    log "WARN: funnel URL not reachable right now ($URL)"
fi

LAST_URL=""
[[ -f "$URL_FILE" ]] && LAST_URL=$(head -n1 "$URL_FILE" 2>/dev/null | tr -d '[:space:]')

if [[ "$URL" != "$LAST_URL" ]]; then
    printf '%s\n' "$URL" > "$URL_FILE"
    MSG=$(printf '🐾 동피랑 X 앱 고정 접속 URL (Tailscale Funnel)\n%s\n\n이 주소는 재시작해도 바뀌지 않습니다. 접속 비밀번호는 기존과 동일.' "$URL")
    if "$PYTHON" "$REPO/scripts/notify_admin.py" "$MSG" >> "$WATCH_LOG" 2>&1; then
        log "admin notified ($URL)"
    else
        log "telegram notify failed (continuing)"
    fi
fi

log "OK $URL"
exit 0
