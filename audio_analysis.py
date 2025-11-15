import pyaudio
import librosa
import numpy as np
from utils import audio_queue
import time
import sys

def analyze_audio():
    try:
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000

        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        print("Audio analysis started.")
        print("Speak or make noise to see audio scores.")

        while True:
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
                audio = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                rms = librosa.feature.rms(y=audio)[0].mean()
                zcr = librosa.feature.zero_crossing_rate(y=audio)[0].mean()
                score = min(100, (rms * 2000 + zcr * 200))
                zone = "room"

                if not audio_queue.full():
                    audio_queue.put((score, zone))
                else:
                    audio_queue.get()
                    audio_queue.put((score, zone))

                time.sleep(0.1)
            except KeyboardInterrupt:
                break

        stream.stop_stream()
        stream.close()
        p.terminate()
        print("Audio analysis stopped.")
    except Exception as e:
        print(f"Error in audio analysis: {e}")
