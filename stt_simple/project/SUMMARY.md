# Summary: Real-time STT Server

## Components
- FastAPI app (`app/main.py`) on port 8000.
- WebSocket `/ws` for audio streaming; HTTP `/health` for liveness; `/` serves a minimal test page.
- STT pipeline (`app/stt.py`) using `faster-whisper` `WhisperModel("base", device="cpu")` with `beam_size=1`, `best_of=1`, VAD on, fixed language (default `"en"`; change in code).

## Data Path
1. Browser page (`/`) captures mic via `AudioContext` + `ScriptProcessor`.
2. Client records via AudioContext at 16 kHz mono, converts to int16 PCM, sends raw PCM chunks over WebSocket.
3. Server buffers raw PCM chunks; when buffer exceeds 65,536 bytes, it transcribes and clears buffer.
4. Transcription result is sent back over WebSocket as JSON: `{"text": str, "duration": float}`.

## Buffering & Threshold
- Accumulates PCM int16 chunks; threshold `> 65536` bytes (~2 seconds of 16 kHz mono int16).
- After each transcription, buffer is cleared to keep latency bounded.

## Frontend Notes
- Minimal HTML test page at `/` with Start/Stop buttons, status, last result, bytes sent, and log.
- Uses `AudioContext` to avoid container decoding issues; sends PCM directly (no WebM decoding).
- Displays `Bytes sent` to indicate when the 32 KB threshold is crossed.

## Model & Quality
- Model: `base` multilingual; beam_size=1, best_of=1, VAD on; language fixed (default `"en"`).
- Audio input expected: mono, 16 kHz, int16 PCM normalized to float32 before transcription.

## Runbook
- Install deps: `python3 -m pip install -r requirements.txt` inside an activated venv.
- Run server: `python3 -m uvicorn app.main:app --reload` (or without `--reload` for stability).
- Test: open `http://localhost:8000/`, click Start, speak 3–6 seconds; after >32 KB sent, text appears.
