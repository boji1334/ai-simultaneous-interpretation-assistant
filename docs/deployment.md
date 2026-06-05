# Deployment And Reproduction

## Local Development

Backend:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -e backend[dev]
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Vite proxies `/api` and `/ws` to `http://127.0.0.1:8000` by default. Set `VITE_API_BASE_URL` only when the backend runs elsewhere.

Open:

```text
http://127.0.0.1:5173
```

## One-Command Windows Startup

```powershell
.\scripts\start-dev.ps1
```

The script starts backend and frontend in hidden windows and prints both PIDs.

Stop local servers:

```powershell
.\scripts\stop-dev.ps1
```

## Verification

Full check:

```powershell
.\scripts\check.ps1
```

Single-service smoke check:

```powershell
.\scripts\smoke-single-service.ps1
```

Manual low-level checks:

```powershell
.\.venv\Scripts\pytest backend
cd frontend
npm run build
```

Browser checks:

- Click `查看 Provider`.
- Optionally test `开始录音` / `停止录音` if microphone permission is available.
- Click `启动实时演示`.
- Confirm `已修正` appears.
- Confirm `注意力机制` appears.
- Confirm `1480ms` correction latency appears.
- Click `加载最终字幕` and confirm the fallback snapshot shows final subtitles, glossary, metrics, correction timeline, and summary.
- Download Markdown and SRT exports.

## Single-Service Mode

For demo deployment, build the frontend first:

```powershell
cd frontend
npm run build
cd ..
```

Then start only FastAPI:

```powershell
.\.venv\Scripts\uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

The backend automatically serves `frontend/dist` when it exists.

For a repeatable review gate, prefer:

```powershell
.\scripts\smoke-single-service.ps1
```

It builds the frontend, starts FastAPI, checks HTTP endpoints and both WebSocket streams, then stops the service.
