# Luna Chat Deluxe

A local Flask client for `gpt-5.6-luna`, retaining ECM-paced text, SQLite history, and the optional semantic cache while adding a small podcast studio.

## Requirements

- Python 3.10+
- An OpenAI API key
- FFmpeg (`brew install ffmpeg` on macOS)

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY='your-key'
python app.py
```

Open `http://127.0.0.1:5000`.

## Use a local LLM

Luna Chat supports an OpenAI-compatible local server (including llama.cpp-style
servers) on loopback port 8080 or 8081. The app adds `/v1` automatically:

```bash
export LUNA_LOCAL_LLM_URL='http://127.0.0.1:8080'
export LUNA_LOCAL_LLM_MODEL='your-local-model-name'
python app.py
```

Use `http://127.0.0.1:8081` for port 8081. A local chat server does not require
`OPENAI_API_KEY`; conversation history is sent through the compatible Chat
Completions API. Hosted speech, transcription, and podcast verification still
require `OPENAI_API_KEY`. You can also set `LUNA_LOCAL_LLM_API_KEY` if your local
server checks an API key.

### Forward an LLM from M3

If the model is listening on M3's loopback port 8080, forward it to this
machine's port 8081 in a separate terminal:

```bash
./scripts/forward_m3_llm.sh
```

The script uses the SSH host alias `M3`. Pass a different SSH destination when
needed, for example `./scripts/forward_m3_llm.sh glen@m3.local`. Keep the tunnel
terminal open while using Luna Chat.

## Test

```bash
pip install -r requirements-dev.txt
pytest
```

## Audio features

- **Speak Aloud** generates and locally caches the selected Luna voice.
- The **Pacing** slider controls text speed and pitch-preserved audio playback speed.
- **Save Recording** exports an individual Luna response at the current paced speed.
- **Export Podcast** gives user prompts the Host voice and Luna responses the Luna voice. It now derives both voice tempo and inter-turn pause timing from the Pacing slider, normalizes the finished program to approximately -16 LUFS, and exports a VBR MP3 whose filename includes the applied speed.
- Synthetic voices should be disclosed as AI-generated when publishing audio.

Audio caches and exports are stored below `data/`.


## Transcript and response controls

- **Response Length** guides Luna from very concise through expansive answers.
- **Export Transcript** downloads exact conversation text as TXT and JSON in a ZIP archive.
- **Export Podcast** also writes TXT, JSON, and SRT sidecars in `data/exports/`.
- When **Verify exported podcast with OpenAI transcription** is enabled, the app sends the finished MP3 to `gpt-4o-transcribe` (configurable with `OPENAI_TRANSCRIBE_MODEL`) and stores a verification transcript beside the authoritative transcript.
