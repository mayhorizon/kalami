# Kalami - 100% FREE Setup Guide

This guide will help you set up Kalami using **completely free, open-source AI models** that run locally on your machine. Zero API costs!

## Overview of Free Stack

| Component | Free Solution | Cost | Requirements |
|-----------|--------------|------|--------------|
| **Speech-to-Text** | OpenAI Whisper (local) | $0 | 2-4GB RAM |
| **Text-to-Speech** | Piper TTS | $0 | 1GB RAM |
| **LLM Conversation** | Ollama + Llama 3.2 | $0 | 2-8GB RAM |
| **Total** | **All Local** | **$0/month** | **5-13GB RAM** |

Compared to paid services:
- OpenAI API: ~$20-50/month
- AssemblyAI: ~$15-30/month
- ElevenLabs: ~$22-99/month
- **Kalami (Free): $0/month** ✅

## Step 1: Install Ollama (LLM)

Ollama lets you run Llama 3 and other AI models locally.

### Installation

**macOS/Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
Download from: https://ollama.com/download

### Start Ollama Server

```bash
ollama serve
```

### Download a Model

Choose based on your RAM:

```bash
# Fastest - 1B parameters (~2GB RAM)
ollama pull llama3.2:1b

# Recommended - 3B parameters (~6GB RAM) ⭐
ollama pull llama3.2:3b

# Best quality - 8B parameters (~16GB RAM)
ollama pull llama3.2

# Alternative - Mistral 7B (~8GB RAM)
ollama pull mistral
```

### Test It

```bash
ollama run llama3.2:3b "Hola, ¿cómo estás?"
```

## Step 2: Install Whisper (Speech-to-Text)

OpenAI's Whisper is free and open-source! It runs locally.

### Installation

```bash
pip install openai-whisper
# Or use the faster version:
pip install faster-whisper
```

### Download Models

Models download automatically on first use:

- **tiny**: ~75MB, fastest
- **base**: ~150MB, good balance ⭐
- **small**: ~500MB, better accuracy
- **medium**: ~1.5GB, high accuracy
- **large**: ~3GB, best accuracy

```python
import whisper
model = whisper.load_model("base")  # Downloads on first run
result = model.transcribe("audio.mp3")
print(result["text"])
```

## Step 3: Install Piper TTS (Text-to-Speech)

Piper is a fast, neural TTS system that runs locally.

### Installation

**Option 1: Download Binary (Recommended)**

1. Download from: https://github.com/rhasspy/piper/releases
2. Extract to `/usr/local/bin/piper` or `C:\Program Files\piper\`

**Option 2: Build from Source**

```bash
git clone https://github.com/rhasspy/piper.git
cd piper/src/cpp
cmake -Bbuild -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

### Download Voice Models

Download voices for your languages:

**Spanish:**
```bash
mkdir -p models/piper_voices
cd models/piper_voices

# Download Spanish voice
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/mls_10246/medium/es_ES-mls_10246-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/mls_10246/medium/es_ES-mls_10246-medium.onnx.json
```

**French:**
```bash
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/mls_1840/medium/fr_FR-mls_1840-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/mls_1840/medium/fr_FR-mls_1840-medium.onnx.json
```

**German:**
```bash
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx.json
```

**English:**
```bash
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
```

Or browse all voices: https://huggingface.co/rhasspy/piper-voices/tree/main

### Test Piper

```bash
echo "Hello, this is a test" | piper \
  --model models/piper_voices/en_US-lessac-medium.onnx \
  --output_file test.wav
```

## Step 4: Setup Kalami Backend

### Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Configure Environment

```bash
cp .env.example .env
```

Edit `.env` to use FREE providers:

```bash
# Use FREE local models
STT_PROVIDER=whisper-local
LLM_PROVIDER=ollama
TTS_PROVIDER=piper

# Model Configuration
WHISPER_MODEL_SIZE=base
OLLAMA_MODEL=llama3.2:3b
PIPER_VOICES_DIR=./models/piper_voices
```

### Start the Backend

```bash
# Make sure Ollama is running first!
ollama serve

# In another terminal:
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

Visit: http://localhost:8000/docs

## Hardware Requirements

### Minimum (for testing):
- **CPU**: Dual-core 2GHz+
- **RAM**: 4GB
- **Disk**: 5GB free space
- **Models**: Whisper tiny, Llama 3.2:1b, Piper

### Recommended (good performance):
- **CPU**: Quad-core 2.5GHz+
- **RAM**: 8GB
- **Disk**: 10GB free space
- **Models**: Whisper base, Llama 3.2:3b, Piper

### Optimal (best quality):
- **CPU**: 6+ cores or GPU
- **RAM**: 16GB+
- **Disk**: 15GB free space
- **Models**: Whisper medium, Llama 3.2 (8b), Piper

## Performance Comparison

| Model Size | Speed | Quality | RAM | Use Case |
|------------|-------|---------|-----|----------|
| **Whisper tiny** | Fastest | Good | 1GB | Real-time testing |
| **Whisper base** | Fast | Better | 1GB | Recommended ⭐ |
| **Whisper small** | Medium | Great | 2GB | High accuracy |
| **Llama 3.2:1b** | Fastest | Good | 2GB | Quick responses |
| **Llama 3.2:3b** | Fast | Great | 6GB | Recommended ⭐ |
| **Llama 3.2 (8b)** | Medium | Excellent | 16GB | Best quality |

## Troubleshooting

### Ollama: "connection refused"
```bash
# Start Ollama server
ollama serve
```

### Whisper: "Model not found"
```python
# Models download automatically on first use
import whisper
model = whisper.load_model("base")  # Will download ~150MB
```

### Piper: Voice model not found
```bash
# Download voice models manually
cd backend/models/piper_voices
# Download .onnx and .onnx.json files from:
# https://huggingface.co/rhasspy/piper-voices/tree/main
```

### Out of Memory
```bash
# Use smaller models:
WHISPER_MODEL_SIZE=tiny
OLLAMA_MODEL=llama3.2:1b
```

## Alternative: Simple Fallback (Even Simpler)

If you want the absolute simplest setup with no downloads:

```bash
# .env
STT_PROVIDER=whisper-local
LLM_PROVIDER=ollama
TTS_PROVIDER=pyttsx3  # Built-in Python TTS (robotic but works)

WHISPER_MODEL_SIZE=tiny
OLLAMA_MODEL=llama3.2:1b
```

This uses:
- Whisper tiny (automatic download)
- Llama 3.2:1b (fastest)
- pyttsx3 (no setup, but robotic voice)

## Cost Comparison

### Free Setup (Kalami):
- **Setup**: One-time download (~3-5GB)
- **Monthly cost**: $0
- **Per conversation**: $0
- **Total first year**: $0 ✅

### Paid API Services:
- OpenAI STT: $0.006/minute
- OpenAI LLM: $0.01/1K tokens
- OpenAI TTS: $0.015/1K characters
- **10 hours/month**: ~$30-50
- **Total first year**: $360-600 ❌

## Next Steps

1. ✅ Install Ollama and pull llama3.2:3b
2. ✅ Test Whisper installation
3. ✅ Download Piper voices for your target languages
4. ✅ Configure `.env` with FREE providers
5. ✅ Start backend and test API
6. 🚀 Build Flutter mobile app

## Resources

- **Ollama**: https://ollama.com/
- **Whisper**: https://github.com/openai/whisper
- **Piper TTS**: https://github.com/rhasspy/piper
- **Piper Voices**: https://huggingface.co/rhasspy/piper-voices
- **Llama 3 Models**: https://ollama.com/library/llama3.2

## Questions?

Open an issue on GitHub: https://github.com/mayhorizon/kalami/issues

---

**Built with 100% free, open-source AI** ❤️
