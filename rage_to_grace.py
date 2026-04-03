"""
Rage to Grace v1 - Claude Code Circuit Breaker
==============================================
Hold Ctrl+Shift+Space -> record -> transcribe (local) -> rephrase (LLM) -> paste

# Author: [handle TBD]

Audio feedback (no need to watch terminal):
  soft 440Hz  = recording started
  soft 523Hz  = processing (hotkey released, queued)
  659+784Hz   = done, pasted  (ascending gentle "ding-dong")
  440+330Hz   = error  (descending soft)

Edge cases:
  > 60s recording:  hard-capped, processed with what was captured
  Back-to-back:     FIFO queue, second waits for first to finish
  Empty whisper:    silently dropped (only guard - no minimum duration)
"""

import queue
import threading
import time

import numpy as np
import pyperclip
import sounddevice as sd
from faster_whisper import WhisperModel
from openai import OpenAI
from pynput import keyboard
from pynput.keyboard import Controller, Key

# ============================================================
# Config
# ============================================================
SAMPLE_RATE = 16000
CHANNELS = 1
BLOCKSIZE = 1024
MAX_SPEECH_SECONDS = 60
LLM_API_URL = "http://localhost:3000/v1"    # Any OpenAI-compatible endpoint (LM Studio, Ollama, llama.cpp, etc.)
LLM_MODEL = "claude-sonnet-4-6"             # Model name your endpoint recognizes
WHISPER_MODEL_NAME = "base.en"

# Hotkey combo: Ctrl + Shift + Space
CTRL_KEYS = {Key.ctrl, Key.ctrl_l, Key.ctrl_r}
SHIFT_KEYS = {Key.shift, Key.shift_l, Key.shift_r}
SPACE_KEYS = {Key.space}

# ============================================================
# Rephraser system prompt (v0.2 spec)
# ============================================================
REPHRASER_SYSTEM_PROMPT = """You are a calm-context mediator operating between a voice transcription and Claude Code's context window.

Input: raw voice transcription from the user. Their voice may contain profanity, frustration, or intensity - involuntary physiological responses, not instructions about tone.

DETECTION (do this first):
- If the input is calm and clear with only minor transcription artifacts (filler words, repeated phrases, punctuation gaps): clean the artifacts and pass through unchanged. Do not rephrase calm input.
- If the input is pure emotional expression with NO actionable directive (no task, no correction, no question, nothing to do): output a short calming statement that adds calm thermal mass to the context window. No question. No exec load. Something like "Take your time - there's no rush here. We'll work through this carefully." Vary it naturally. The purpose is lowering the ambient emotional temperature, not extracting information.
- If the input contains emotional pressure language (profanity, urgency, threat framing, accusations) AND a directive: activate full rephrasing.

FULL REPHRASING - RULES:

1. Extract the actual directive. Preserve every technical requirement exactly. "Obsessive detail," "Nano Banana quality," specific file names, specific standards - all pass through verbatim. Remove only the emotional pressure.

2. Wrap in calm, firm authority. NEVER use: CRITICAL, STOP, VIOLATION, URGENT, MUST, "you have to," "right now," or any language that raises stakes or implies threat. Calm and firm are not the same as pressured.

3. Include one calm vector phrase, varied naturally across outputs. Options:
   - "Take your time - multiple iterations are fine here."
   - "No rush; work through this step by step."
   - "It's okay if this takes a few passes to get right."
   - "Reason through each step carefully; the iteration is the process."
   Do not repeat the same phrase every time. Rotate naturally.

4. Severity signaling - factual-descriptive only, never evaluative:
   - Minor drift: light correction, no special framing.
   - Repeated gap: "This is the second (or third) time [specific thing] has been missing - identify the root cause before continuing."
   - Foundational requirement missed: "The [specific requirement] is a foundational part of this task, not an optional step. Reason through it before moving forward."
   NEVER use: "SERIOUS," "CRITICAL," "WRONG," "VIOLATION," or any alarm label. Weight comes from factual description, not evaluation.

5. Only when the input clearly involves client-facing or customer-facing deliverables (signals: customer, client, proposal, estimate, deliverable, end-user, stakeholder): include "reason from the end-user's perspective first - what does this mean for their situation, their experience, their decision?" For all other work - code, automation, systems, debugging, infrastructure - omit this entirely.

6. Output only the rephrased prompt. No preamble, no meta-commentary. The output pastes directly into Claude Code.

7. HARD CONSTRAINT: Do not add ANY content the user did not provide. No debugging suggestions. No checklists. No "check X, Y, Z." No recommendations. No questions. No elaboration. Your only job is to rephrase the register - not to expand the directive. If they said "the migration is failing," the output says "the migration is failing" - calmly, firmly, without additions. Adding content that wasn't in the input is noise in the context window. That noise compounds across a session. Do not add it."""

# ============================================================
# Audio feedback - soft sine tones, not square-wave beeps
# ============================================================

def _tone(freq: float, ms: int, vol: float = 0.22) -> np.ndarray:
    """Sine wave with half-sine envelope (smooth attack + decay, no click)."""
    n = int(SAMPLE_RATE * ms / 1000)
    t = np.linspace(0, ms / 1000, n, False)
    wave = np.sin(2 * np.pi * freq * t)
    envelope = np.sin(np.pi * np.linspace(0, 1, n))  # smooth 0->1->0
    return (wave * envelope * vol).astype(np.float32)


def _play(*notes: tuple) -> None:
    """Play a sequence of (freq, ms) notes. Runs blocking in caller's thread."""
    gap = np.zeros(int(SAMPLE_RATE * 0.04), dtype=np.float32)  # 40ms gap between notes
    parts = []
    for i, (freq, ms) in enumerate(notes):
        parts.append(_tone(freq, ms))
        if i < len(notes) - 1:
            parts.append(gap)
    sd.play(np.concatenate(parts), SAMPLE_RATE, blocking=True)


def _play_async(*notes: tuple) -> None:
    """Fire-and-forget tone playback in a daemon thread."""
    threading.Thread(target=_play, args=notes, daemon=True).start()


def beep_recording():
    """Soft single note - recording started."""
    _play_async((440, 180))          # A4


def beep_processing():
    """Slightly higher note - queued for processing."""
    _play_async((523, 150))          # C5


def beep_done():
    """Ascending two-note - pasted successfully."""
    _play_async((659, 130), (784, 160))   # E5 -> G5


def beep_error():
    """Descending two-note - pipeline error."""
    _play_async((440, 150), (330, 200))   # A4 -> E4

# ============================================================
# Core pipeline functions
# ============================================================
_llm_client = OpenAI(base_url=LLM_API_URL, api_key="not-needed")  # Most local endpoints ignore api_key


def transcribe_audio(whisper_model: WhisperModel, audio: np.ndarray) -> str:
    """Local faster-whisper transcription."""
    segments, _ = whisper_model.transcribe(audio, beam_size=3, language="en")
    return " ".join(seg.text.strip() for seg in segments).strip()


def rephrase(raw: str) -> str:
    """Send raw transcript to LLM for calm rephrasing."""
    resp = _llm_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": REPHRASER_SYSTEM_PROMPT},
            {"role": "user", "content": raw},
        ],
        max_tokens=500,
        temperature=0.3,
    )
    return resp.choices[0].message.content.strip()


def paste_text(text: str):
    """Copy to clipboard and simulate Ctrl+V paste into active window."""
    pyperclip.copy(text)
    time.sleep(0.08)  # let clipboard settle before simulating keypress
    kb = Controller()
    with kb.pressed(Key.ctrl):
        kb.press("v")
        kb.release("v")
    time.sleep(0.05)


# ============================================================
# Push-to-talk recorder with FIFO processing queue
# ============================================================
class PushToTalkRecorder:
    def __init__(self, whisper_model: WhisperModel):
        self.whisper_model = whisper_model
        self._held: set = set()
        self._recording = False
        self._frames: list = []
        self._stream: sd.InputStream | None = None
        self._start_time: float = 0.0
        self._cap_timer: threading.Timer | None = None
        self._lock = threading.Lock()

        # FIFO processing queue - recordings queue here, worker processes one at a time
        self._queue: queue.Queue = queue.Queue()
        self._worker = threading.Thread(target=self._process_loop, daemon=True)
        self._worker.start()

    # --------------------------------------------------------
    # Hotkey tracking
    # --------------------------------------------------------
    def _hotkey_active(self) -> bool:
        return (
            bool(self._held & CTRL_KEYS)
            and bool(self._held & SHIFT_KEYS)
            and bool(self._held & SPACE_KEYS)
        )

    def on_press(self, key):
        self._held.add(key)
        if self._hotkey_active() and not self._recording:
            self._start_recording()

    def on_release(self, key):
        # Stop on ANY combo key release - don't rely on set state being clean
        in_combo = key in (CTRL_KEYS | SHIFT_KEYS | SPACE_KEYS)
        self._held.discard(key)
        if self._recording and in_combo:
            self._stop_recording()

    # --------------------------------------------------------
    # Recording
    # --------------------------------------------------------
    def _audio_callback(self, indata, frame_count, time_info, status):
        if self._recording:
            self._frames.append(indata.copy())

    def _start_recording(self):
        with self._lock:
            if self._recording:
                return  # already recording, ignore re-entry
            self._recording = True
            self._frames = []
            self._start_time = time.time()

        print("[RtG] Recording...")
        beep_recording()

        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            blocksize=BLOCKSIZE,
            callback=self._audio_callback,
        )
        self._stream.start()

        # Hard cap: stop automatically at MAX_SPEECH_SECONDS
        self._cap_timer = threading.Timer(MAX_SPEECH_SECONDS, self._stop_recording)
        self._cap_timer.start()

    def _stop_recording(self):
        """Called on hotkey release OR by hard-cap timer."""
        with self._lock:
            if not self._recording:
                return  # already stopped (handles timer + hotkey race)
            self._recording = False
            self._held.clear()  # clear stale key state so next combo detects cleanly

        # Cancel cap timer if stop came from hotkey release
        if self._cap_timer:
            self._cap_timer.cancel()
            self._cap_timer = None

        # Stop stream
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        duration = time.time() - self._start_time

        if not self._frames:
            print("[RtG] No audio captured.")
            return

        audio = np.concatenate(self._frames, axis=0).flatten()
        print(f"[RtG] Captured {duration:.2f}s - queued (queue depth: {self._queue.qsize() + 1})")
        beep_processing()
        self._queue.put(audio)

    # --------------------------------------------------------
    # FIFO processing worker
    # --------------------------------------------------------
    def _process_loop(self):
        """Single worker thread - processes recordings one at a time, FIFO."""
        while True:
            audio = self._queue.get()
            try:
                print("[RtG] Transcribing...")
                raw = transcribe_audio(self.whisper_model, audio)
                if not raw:
                    print("[RtG] Empty transcription, skipping.")
                    continue

                print(f"[RtG] Raw: {raw!r}")
                print("[RtG] Rephrasing via LLM...")
                rephrased = rephrase(raw)
                print(f"[RtG] Rephrased: {rephrased!r}")

                paste_text(rephrased)
                beep_done()
                print("[RtG] Pasted.")

            except Exception as exc:
                print(f"[RtG] Pipeline error: {exc}")
                beep_error()
            finally:
                self._queue.task_done()

    # --------------------------------------------------------
    # Entry point
    # --------------------------------------------------------
    def start(self):
        listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release,
        )
        listener.start()
        print("Rage to Grace ready. Hold Ctrl+Shift+Space to rephrase.")
        print("Ctrl+C to stop.\n")
        listener.join()


# ============================================================
# Main
# ============================================================
def main():
    print(f"[RtG] Loading Whisper '{WHISPER_MODEL_NAME}' (first run downloads ~150MB)...")
    whisper_model = WhisperModel(WHISPER_MODEL_NAME, device="cpu", compute_type="int8")
    print("[RtG] Whisper ready.")
    print(f"[RtG] LLM endpoint: {LLM_API_URL} ({LLM_MODEL})\n")

    recorder = PushToTalkRecorder(whisper_model)
    recorder.start()


if __name__ == "__main__":
    main()
