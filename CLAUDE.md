# Exercise Checker — Project Instructions

## Overview
Mobile app that records a workout video, analyses pose landmarks, and gives form feedback.
- **Mobile:** React Native (Expo) — `mobile/`
- **Backend:** Python FastAPI — `backend/`

## Architecture
- No database, no auth, stateless per request
- MediaPipe Tasks API (`PoseLandmarker`, VIDEO mode) runs on the backend
- Form logic is rule-based angle checks — no ML training
- Single endpoint: `POST /analyze` (multipart: `exercise` + `video`)

## Supported exercises
- `pushups` — elbow angle at bottom (~90°), back straightness
- `squats` — knee angle at bottom (~90°), knee-over-toe, torso lean
- `bicep_curls` — elbow fixed at side, full ROM (extended ≥150°, contracted ≤50°)

## Key files
| File | Purpose |
|------|---------|
| `backend/main.py` | FastAPI app, `/analyze` endpoint |
| `backend/pose_extractor.py` | MediaPipe Tasks PoseLandmarker, VIDEO mode |
| `backend/exercises/pushups.py` | Push-up form logic |
| `backend/exercises/squats.py` | Squat form logic |
| `backend/exercises/bicep_curls.py` | Bicep curl form logic |
| `mobile/app/index.tsx` | Screen 1: exercise picker |
| `mobile/app/record.tsx` | Screen 2: record/upload + submit |
| `mobile/app/results.tsx` | Screen 3: pass/fail + feedback |
| `mobile/src/api.ts` | Fetch wrapper with error handling |
| `mobile/src/config.ts` | `EXPO_PUBLIC_API_URL` config |

## MediaPipe
- Uses **Tasks API** (`mp.tasks.vision.PoseLandmarker`), NOT the deprecated Solutions API (`mp.solutions.pose`)
- Model: `pose_landmarker_full.task` — auto-downloaded to `backend/` on first run
- Running mode: `VIDEO` — must pass monotonically increasing `timestamp_ms`

## Running locally

### Backend
```bash
python -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Mobile
```bash
cd mobile
npm install
cp .env.example .env   # set EXPO_PUBLIC_API_URL to LAN IP for physical devices
npx expo start -c
```

## Constraints
- Video max size: 100 MB (enforced in backend)
- Video max duration: 60 s (enforced by expo-image-picker)
- 3 screens max: Home, Record/Upload, Results
- No real-time streaming, no persistence
