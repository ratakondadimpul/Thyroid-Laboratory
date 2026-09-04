#!/bin/zsh
# Start Thyroid Lab Intelligence
set -e
ROOT=$(cd "$(dirname "$0")" && pwd)
echo "Starting backend on http://127.0.0.1:8000 ..."
nohup python3 -m uvicorn app.main:app --app-dir "$ROOT/backend" --host 127.0.0.1 --port 8000 > /tmp/thyroid_backend.log 2>&1 & echo "  backend PID $!"
sleep 3
curl -s http://127.0.0.1:8000/health | head -c 300; echo
echo "Starting frontend on http://127.0.0.1:3001 ..."
nohup npm run dev --prefix "$ROOT/frontend" > /tmp/thyroid_frontend.log 2>&1 & echo "  frontend PID $!"
sleep 5
echo "Done."
echo "  Frontend: http://127.0.0.1:3001  (login: admin@lab.local / admin123)"
echo "  Backend:  http://127.0.0.1:8000/docs"
echo "  Sample file: frontend/public/sample_lab.csv"
echo "Logs: /tmp/thyroid_backend.log /tmp/thyroid_frontend.log"
echo "Stop: pkill -f 'uvicorn app.main:app' ; pkill -f 'next-server'"
