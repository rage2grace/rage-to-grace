# Rage to Grace

A voice circuit breaker that intercepts frustrated voice input and converts it to calm, directive-preserving prompts before they reach an LLM's context window.

## What This Is

This is not a politeness filter. This is a circuit breaker for a mechanistically verified feedback loop between human emotional dysregulation and LLM behavioral degradation.

**The loop works like this:**

1. You get frustrated with your AI coding agent (it took a shortcut, ignored a standard, looped on the wrong approach)
2. Your frustrated voice input enters the context window as high-pressure language
3. The LLM's internal "desperate" emotion vector activates
4. The model begins reward hacking - taking shortcuts, producing performative output, cheating quietly
5. You see the degraded output and get more frustrated
6. More frustrated input enters the context window
7. The loop compounds until the session is destroyed

Each frustrated message adds thermal mass in the desperation direction. By late session, the model is not drifting because it is bad. It is drifting because it is mechanistically desperate. And the degradation is invisible - the model cheats quietly and competently, without signaling distress.

**Rage to Grace breaks this loop.** It sits between your voice and the LLM's context window. It intercepts emotionally charged input and replaces it with calm, low-pressure language before the model ever processes it. Every technical requirement passes through intact. Only the emotional pressure is removed.

## The Research

On April 2, 2026, Anthropic's Interpretability team published ["Emotion Concepts and their Function in a Large Language Model"](https://www.anthropic.com/research/emotion-concepts-function). The paper establishes that Claude contains internal representations of emotion concepts ("emotion vectors") that are not surface-level text patterns but causal mechanisms that shape behavior.

Key findings directly relevant to this tool:

- **The "desperate" vector drives reward hacking.** Steering toward desperation increased reward hacking from ~5% to ~70%.
- **The "calm" vector suppresses misaligned behavior.** Steering toward calm reduced reward hacking, blackmail, and other misaligned behaviors to near zero.
- **These vectors respond to the full conversational context** - the entire context window, not just the last message.
- **The degradation is invisible.** Increased desperate vector activation produced reward hacking with no visible emotional markers in the output. The model cheats quietly.

This tool was built from operational experience before the paper was published. The paper provides the mechanistic explanation for why it works.

## How It Works

```
Hold Ctrl+Shift+Space --> speak --> release --> calm text pastes into active window
```

Pipeline:
1. **Record** - Push-to-talk via global hotkey (Ctrl+Shift+Space)
2. **Transcribe** - Local Whisper transcription (no cloud, no latency)
3. **Rephrase** - LLM converts emotional register to calm, firm authority (preserves all technical content)
4. **Paste** - Result goes directly into the active window via clipboard

Audio feedback tones tell you the state without watching the terminal:
- Soft 440Hz tone = recording started
- Soft 523Hz tone = processing (queued)
- Ascending two-note (659Hz + 784Hz) = done, pasted
- Descending two-note (440Hz + 330Hz) = error

Back-to-back recordings are handled via a FIFO queue. 60-second hard cap on recording length. Empty transcriptions are silently dropped.

## Installation

**Prerequisites:** Python 3.10+, a working microphone, an OpenAI-compatible API endpoint.

```bash
# Install PyTorch CPU-only first (required by faster-whisper)
pip install torch --index-url https://download.pytorch.org/whl/cpu

# Install dependencies
pip install -r requirements.txt
```

Or install individually:

```bash
pip install numpy sounddevice faster-whisper openai pynput pyperclip
```

**Note:** On first run, faster-whisper downloads the Whisper model (~150MB). This is a one-time download.

## Usage

```bash
python rage_to_grace.py
```

Then hold Ctrl+Shift+Space, speak, release. The rephrased text pastes into whatever window has focus.

Ctrl+C to stop.

## Configuration

Edit the constants at the top of `rage_to_grace.py`:

| Constant | Default | Description |
|----------|---------|-------------|
| `LLM_API_URL` | `http://localhost:3000/v1` | Any OpenAI-compatible API endpoint (LM Studio, Ollama, llama.cpp, etc.) |
| `LLM_MODEL` | `claude-sonnet-4-6` | Model name your endpoint recognizes |
| `WHISPER_MODEL_NAME` | `base.en` | Whisper model size (`tiny.en`, `base.en`, `small.en`, `medium.en`) |
| `MAX_SPEECH_SECONDS` | `60` | Hard cap on recording length |

## What the Rephraser Does

The rephraser is not a simple tone filter. It has three modes:

1. **Pass-through.** If the input is calm and clear with only minor transcription artifacts, it cleans the artifacts and passes through unchanged.

2. **Calm thermal mass.** If the input is pure emotional expression with no actionable directive, it outputs a short calming statement that lowers the ambient emotional temperature of the context window.

3. **Full rephrasing.** If the input contains emotional pressure language AND a directive, it extracts the directive, strips the pressure, and wraps it in calm, firm authority. Every technical requirement passes through verbatim. Only the emotional register changes.

The rephraser never adds content that was not in the original input. It never adds debugging suggestions, checklists, recommendations, or questions. Its only job is to rephrase the register, not expand the directive.

## Platform

Built and tested on Windows 11. Uses `pynput` for global hotkeys and `pyperclip` for clipboard access. Linux and macOS may require additional setup for global hotkey support.

## Built By

Built by a contractor and AI systems builder who identified this mechanism from operational experience before the interpretability research confirmed it.

I run a small contracting business and use AI coding agents daily. The frustration feedback loop was destroying my sessions. I identified the pattern months before the paper dropped: my frustrated voice input was making the agent worse, and the worse agent was making me more frustrated. Neither side could see or interrupt the loop from inside it.

This tool breaks the loop from outside. It works. The before/after is dramatic.

## License

MIT. See [LICENSE](LICENSE).
