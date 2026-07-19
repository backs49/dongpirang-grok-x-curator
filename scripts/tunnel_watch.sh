#!/bin/bash
# Cloudflare Quick Tunnel 워처 — launchd가 1시간마다 호출 (ai-trader 패턴 이식).
#
# 동작:
# 1. 로컬 앱(8501)이 죽어 있으면 streamlit부터 살린다.
# 2. logs/cloudflared.url의 기존 터널 URL을 curl로 검증.
# 3. 죽었으면 cloudflared 재시작 → 새 trycloudflare URL 캡처 →
#    scripts/notify_admin.py로 **관리자에게만** 텔레그램 발송.
#
# 수동 실행: bash scripts/tunnel_watch.sh
set -u

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$REPO/logs"
URL_FILE="$LOG_DIR/cloudflared.url"
PID_FILE="$LOG_DIR/cloudflared.pid"
OUT_FILE="$LOG_DIR/cloudflared.out"
WATCH_LOG="$LOG_DIR/tunnel-watch.log"
PORT=8501   # 주의: 8502는 ai-trader 대시보드가 사용 중
CLOUDFLARED_BIN="/opt/homebrew/bin/cloudflared"
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

is_alive() {
    local url="$1"
    [[ -n "$url" ]] || return 1
    curl -sf -o /dev/null --max-time 10 "$url"
}

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

restart_cloudflared() {
    log "restarting cloudflared"
    if [[ -f "$PID_FILE" ]]; then
        local old_pid
        old_pid=$(cat "$PID_FILE" 2>/dev/null || echo "")
        if [[ -n "$old_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
            kill "$old_pid" 2>/dev/null || true
            sleep 2
            kill -9 "$old_pid" 2>/dev/null || true
        fi
    fi
    pkill -f "cloudflared tunnel --url http://localhost:$PORT" 2>/dev/null || true
    sleep 1

    : > "$OUT_FILE"
    "$CLOUDFLARED_BIN" tunnel --url "http://localhost:$PORT" --no-autoupdate \
        > "$OUT_FILE" 2>&1 &
    local new_pid=$!
    echo "$new_pid" > "$PID_FILE"
    log "started cloudflared pid=$new_pid"

    local deadline=$((SECONDS + 60))
    local new_url=""
    while (( SECONDS < deadline )); do
        new_url=$(grep -Eo 'https://[A-Za-z0-9-]+\.trycloudflare\.com' "$OUT_FILE" \
            | head -1)
        [[ -n "$new_url" ]] && break
        sleep 2
    done
    if [[ -z "$new_url" ]]; then
        log "ERROR: cloudflared started but no trycloudflare URL appeared in 60s"
        return 1
    fi
    local probe_deadline=$((SECONDS + 30))
    while (( SECONDS < probe_deadline )); do
        if is_alive "$new_url"; then
            break
        fi
        sleep 2
    done
    printf '%s\n' "$new_url" > "$URL_FILE"
    log "new URL: $new_url"

    # 관리자에게만 발송 (notify_admin.py 는 게스트 개념 자체가 없음)
    local msg
    msg=$(printf '🐾 동피랑 X 앱 새 접속 URL\n%s\n\n접속 비밀번호는 기존과 동일' "$new_url")
    if "$PYTHON" "$REPO/scripts/notify_admin.py" "$msg" >> "$WATCH_LOG" 2>&1; then
        log "admin notified ($new_url)"
    else
        log "telegram notify failed (continuing)"
    fi
    return 0
}

ensure_app || exit 1

CURRENT_URL=""
[[ -f "$URL_FILE" ]] && CURRENT_URL=$(head -n1 "$URL_FILE" 2>/dev/null | tr -d '[:space:]')

if is_alive "$CURRENT_URL"; then
    log "OK $CURRENT_URL"
    exit 0
fi

log "tunnel down (url=${CURRENT_URL:-<none>}) — restarting"
if restart_cloudflared; then
    log "restart succeeded"
    exit 0
fi
log "restart FAILED"
exit 1
