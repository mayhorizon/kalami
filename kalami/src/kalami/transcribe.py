# transcribe_file.py
import argparse
import os
import subprocess
import tempfile
from pathlib import Path

from deepspeech import Model
from pydub import AudioSegment
import numpy as np
import wave

def convert_to_wav16mono(in_bytes, out_path):
    audio = AudioSegment.from_file(in_bytes)
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    audio.export(out_path, format="wav")
    return out_path

def transcribe(model_path, scorer_path, audio_path):
    ds = Model(model_path)
    if scorer_path:
        ds.enableExternalScorer(scorer_path)

    with wave.open(audio_path, 'rb') as wf:
        frames = wf.getnframes()
        buffer = wf.readframes(frames)
        # DeepSpeech expects 16-bit PCM little endian
        text = ds.stt(buffer)
    return text

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True, help="Path to .pbmm (or .pb) model file")
    p.add_argument("--scorer", required=False, help="Path to external scorer (.scorer)")
    p.add_argument("--input", required=True, help="Input audio file (wav/mp3/ogg/m4a)")
    args = p.parse_args()

    # convert to 16k mono wav in a temp file
    tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp_wav.close()
    convert_to_wav16mono(args.input, tmp_wav.name)

    text = transcribe(args.model, args.scorer, tmp_wav.name)
    print("Transcription:\n", text)

    os.unlink(tmp_wav.name)

if __name__ == "__main__":
    main()
