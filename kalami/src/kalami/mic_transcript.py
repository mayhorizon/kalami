# transcribe_mic.py
import queue
import sys
import threading
import signal

import pyaudio
from deepspeech import Model
import numpy as np

MODEL_PATH = "models/deepspeech-0.9.3-models.pbmm"
SCORER_PATH = "models/deepspeech-0.9.3-models.scorer"

# audio params
RATE = 16000
CHUNK = 1024  # number of frames per buffer

q = queue.Queue()

def audio_callback(in_data, frame_count, time_info, status):
    q.put(in_data)
    return (None, pyaudio.paContinue)

def main():
    ds = Model(MODEL_PATH)
    ds.enableExternalScorer(SCORER_PATH)

    stream_context = ds.createStream()

    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK,
                        stream_callback=audio_callback)

    print("Listening (press Ctrl+C to stop)...")
    stream.start_stream()

    try:
        while True:
            data = q.get()
            stream_context.feedAudioContent(np.frombuffer(data, dtype=np.int16))
            # You can print interim results:
            interim = stream_context.intermediateDecode()
            if interim:
                print("\rInterim: " + interim, end="")
    except KeyboardInterrupt:
        print("\nFinalizing...")
        text = stream_context.finishStream()
        print("\nFinal transcription:\n", text)
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()

if __name__ == "__main__":
    main()
