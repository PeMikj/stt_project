from typing import Iterable

import numpy as np
from faster_whisper import WhisperModel

LANGUAGE = "en"  # set explicitly; change to "ru" if needed

# Load a multilingual model for good quality.
model = WhisperModel("base", device="cpu")


def transcribe_buffer(chunks: Iterable[bytes]) -> tuple[str, float]:
    """
    Transcribe a sequence of PCM int16 chunks (16 kHz mono) using the loaded Whisper model.

    Returns a tuple of (text, duration_seconds).
    """
    raw = b"".join(chunks)
    if not raw:
        return "", 0.0

    audio_int16 = np.frombuffer(raw, dtype=np.int16)
    if audio_int16.size == 0:
        return "", 0.0

    # Normalize to float32 in [-1, 1].
    audio = (audio_int16.astype(np.float32) / 32768.0).copy()

    segments, info = model.transcribe(
        audio,
        beam_size=1,
        best_of=1,
        language=LANGUAGE,
        vad_filter=True,
    )
    text = "".join(segment.text for segment in segments)
    duration = float(info.duration) if info and info.duration else audio.shape[0] / 16000.0
    return text, duration
