# Exercise Checker

A mobile app that records a short workout video, analyses your movement using MediaPipe pose landmarks, and tells you whether your form is correct.

**Supported exercises:** Push-ups · Squats · Bicep Curls

---

## Project structure

```
exercise_checker/
├── backend/          # FastAPI + MediaPipe
│   ├── main.py
│   ├── pose_extractor.py
│   ├── exercises/
│   │   ├── pushups.py
│   │   ├── squats.py
│   │   └── bicep_curls.py
│   ├── requirements.txt
│   └── .env.example
└── mobile/           # Expo (React Native)
    ├── app/
    │   ├── _layout.tsx
    │   ├── index.tsx   # Home — exercise picker
    │   ├── record.tsx  # Record / upload screen
    │   └── results.tsx # Results screen
    ├── src/
    │   ├── api.ts
    │   └── config.ts
    ├── package.json
    └── .env.example
```

---

## Backend setup

### Requirements
- Python 3.11+

### Steps

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r backend/requirements.txt

cp backend/.env.example backend/.env

python -c "from backend.pose_extractor import download_model; download_model()"

python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

### API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/analyze` | Analyse exercise video |

**POST /analyze** — `multipart/form-data`

| Field | Type | Values |
|-------|------|--------|
| `exercise` | string | `pushups`, `squats`, `bicep_curls` |
| `video` | file | Any video format OpenCV can decode (mp4, mov, …) |

**Response**
```json
{
  "exercise": "pushups",
  "passed": false,
  "feedback": [
    "Go lower — your elbows only reached 120° (aim for ~90°).",
    "Keep your back flat — detected a 25° sag in your hips."
  ]
}
```

---

## Mobile setup

### Requirements
- Node.js 18+
- Expo Go app on your device, or a simulator

### Steps

```bash
cd mobile

npm install

cp .env.example .env

npx expo start
```

Scan the QR code with Expo Go (Android) or the Camera app (iOS).

---

## Form logic

All checks are rule-based on MediaPipe landmark angles — no ML model training required.

| Exercise | Checks |
|----------|--------|
| **Push-ups** | Elbow angle at bottom (~90°), back straightness (hip-shoulder-ankle alignment) |
| **Squats** | Knee angle at bottom (~90°), knee-over-toe alignment, torso lean |
| **Bicep Curls** | Elbow fixed at side, full range of motion (extended ≥150°, contracted ≤50°) |

---

## Error handling

| Scenario | Behaviour |
|----------|-----------|
| Video > 100 MB | HTTP 413 from backend |
| Video > 60 s | Rejected by expo-image-picker before upload |
| No person detected | HTTP 422 with descriptive message |
| Backend unreachable | Alert shown in app with hint to check network |
| Request timeout (>60 s) | Alert shown in app |
