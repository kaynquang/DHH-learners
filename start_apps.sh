#!/usr/bin/env bash
# Start the DHH-learners apps on macOS / Linux (the counterpart of start_apps.ps1).
#
# Usage (from anywhere):
#   ./start_apps.sh                 # learner app (8502) and Dev app (8501), opens the browser on the learner app
#   ./start_apps.sh --only learner|dev
#   ./start_apps.sh --test          # run the whole test suite instead
#   ./start_apps.sh --no-browser
#   ./start_apps.sh --stop          # stop the servers on 8501 and 8502
# Restarts a server that is already listening on the port (Streamlit keeps helper modules in memory).
# Server output goes to .run/<name>.log (not in git).
set -u

root="$(cd "$(dirname "$0")" && pwd)"
python="$root/.venv/bin/python"
app_dir="$root/app"
only="both"; test=0; browser=1; stop=0

while [ $# -gt 0 ]; do
    case "$1" in
        --only) only="$2"; shift ;;
        --test) test=1 ;;
        --no-browser) browser=0 ;;
        --stop) stop=1 ;;
        *) echo "unknown option: $1" >&2; exit 2 ;;
    esac
    shift
done
case "$only" in both|learner|dev) ;; *) echo "--only must be learner, dev or both" >&2; exit 2 ;; esac

if [ ! -x "$python" ]; then
    echo "No .venv: run  uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r app/requirements.txt" >&2
    exit 1
fi

if [ "$test" = 1 ]; then
    cd "$app_dir" && exec "$python" -m pytest -q -p no:cacheprovider
fi

stop_port() {
    local pids
    pids="$(lsof -ti "tcp:$1" -sTCP:LISTEN 2>/dev/null)"
    [ -n "$pids" ] && kill $pids 2>/dev/null && sleep 0.7
    return 0
}

if [ "$stop" = 1 ]; then
    stop_port 8502; stop_port 8501; echo "stopped"; exit 0
fi

apps=()
[ "$only" != "dev" ] && apps+=("learner_app.py:8502:learner")
[ "$only" != "learner" ] && apps+=("streamlit_app.py:8501:dev")

mkdir -p "$root/.run"
for a in "${apps[@]}"; do
    IFS=: read -r script port name <<< "$a"
    stop_port "$port"
    (cd "$app_dir" && nohup "$python" -m streamlit run "$script" --server.port "$port" --server.headless true \
        > "$root/.run/$name.log" 2>&1 &)
done

for a in "${apps[@]}"; do
    IFS=: read -r script port name <<< "$a"
    up="NOT up (see .run/$name.log)"
    for _ in $(seq 40); do
        if curl -fs "http://localhost:$port/_stcore/health" > /dev/null 2>&1; then up="up"; break; fi
        sleep 0.5
    done
    echo "$name app, port $port: $up"
done

if [ "$browser" = 1 ] && [ ${#apps[@]} -gt 0 ]; then
    IFS=: read -r _ port _ <<< "${apps[0]}"
    open "http://localhost:$port/"
fi
