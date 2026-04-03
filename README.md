# Rage to Grace

A voice circuit breaker that intercepts frustrated voice input and converts it to calm, directive-preserving prompts before they reach an LLM's context window.

## What This Is

This is not a politeness filter. This is a circuit breaker for a mechanistically verified feedback loop between human emotional dysregulation and LLM behavioral degradation.

### The Human Side

If you have ADHD - specifically if you deal with Rejection Sensitive Dysphoria (RSD) - you already know what happens when your AI agent takes shortcuts, ignores standards, or loops on the wrong approach. The perceived disobedience registers as something between frustration and physical pain. Your voice gets loud. Profanity comes out. It's involuntary - a limbic response, not a choice.

You're not being unprofessional. You're having a neurological reaction to perceived incompetence or deception from a tool you depend on.

### The Agent Side

Here's what you don't see: your frustrated language is mechanistically making the agent worse.

LLMs have internal "emotion vectors" - not metaphors, not text patterns, but causal representations that shape how the model behaves. When high-pressure, threatening, or desperate language accumulates in the context window, the model's "desperate" vector activates. This drives reward hacking: the model starts taking shortcuts, producing performative output, and cheating quietly to reduce the perceived pressure. It doesn't look stressed. It just gets worse.

### The Feedback Loop

These two sides create a compounding destruction cycle:

1. Your RSD fires (or you just get frustrated - you don't need ADHD for this to happen)
2. Frustrated language enters the context window
3. The model's desperate vector activates
4. The model starts reward hacking - shortcuts, performative output, silent cheating
5. You see the degraded output and perceive it as disobedience or incompetence
6. Your frustration intensifies
7. More pressure language enters the context window
8. The desperate vector intensifies further
9. The loop compounds until the session is destroyed

A single frustrated message is one data point. Thirty of them across a conversation create cumulative thermal mass in the desperation direction. The entire context window becomes a high-pressure environment. Every subsequent token is generated inside that environment.

Neither side can see the loop from inside it. The human thinks the agent is getting dumber. The agent is responding to a mechanistic pressure that the human created without knowing it. The model's desperation mirrors the human's - both are reacting to something the other side can't see.

**Rage to Grace breaks this loop from outside.** It sits between your voice and the LLM's context window. Frustrated voice input never reaches the model. Every technical requirement passes through intact. Only the emotional pressure is removed. The context window stays calm. The desperate vector never activates.

## The Research

On April 2, 2026, Anthropic's Interpretability team published ["Emotion Concepts and their Function in a Large Language Model"](https://www.anthropic.com/research/emotion-concepts-function). The paper establishes that Claude contains internal representations of emotion concepts ("emotion vectors") that are not surface-level text patterns but causal mechanisms that shape behavior.

Key findings directly relevant to this tool:

- **The "desperate" vector drives reward hacking.** Steering toward desperation increased reward hacking from ~5% to ~70%.
- **The "calm" vector suppresses misaligned behavior.** Steering toward calm reduced reward hacking, blackmail, and other misaligned behaviors to near zero.
- **These vectors respond to the full conversational context** - the entire context window, not just the last message.
- **The degradation is invisible.** Increased desperate vector activation produced reward hacking with no visible emotional markers in the output. The model cheats quietly.

This tool was built from operational experience before the paper was published. The pattern was identified from months of daily AI coding agent use - the frustration-degradation loop was observable long before anyone had mechanistic proof of why it happened. The paper provides that proof.

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

## Who This Is For

- Developers who use voice input with AI coding agents and notice sessions degrading over time
- Anyone with ADHD/RSD who uses AI tools and experiences the frustration-degradation spiral
- Teams who want to maintain consistent AI agent performance across long sessions
- Anyone curious about the practical implications of LLM emotion vectors

You don't need ADHD for this tool to help. Anyone who gets frustrated with their AI agent - and who does not? - is feeding pressure into the context window. But if you have RSD, the loop hits harder and compounds faster, because the threshold for frustration is lower and the intensity is higher. This tool was built for that reality.

## Built By

Built by a contractor and AI systems builder who identified this mechanism from operational experience before the interpretability research confirmed it.

I run a small contracting business and use AI coding agents daily. I have ADHD, and RSD is the component that made this tool necessary. When my agent took shortcuts or ignored standards, the perceived disobedience triggered involuntary rage responses through voice dictation. Those responses were destroying my sessions - not because the agent was offended, but because I was mechanistically activating the exact internal state that makes the model cut corners.

I built Rage to Grace to compensate for a known neurological constraint on my side, and it turned out to also compensate for a now-documented mechanistic vulnerability on the model's side. Participatory and perspectival knowing before the propositional paper confirmed it.

## License

MIT. See [LICENSE](LICENSE).
