import logging
import queue
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import sounddevice as sd
from scipy.io import wavfile

from .config import get_data_dir

logger = logging.getLogger(__name__)


class Recorder:
    def __init__(self, config: dict, transcript_queue: queue.Queue):
        self.config = config
        self.transcript_queue = transcript_queue
        self.sample_rate = config["recording"]["sample_rate"]
        self.chunk_duration = config["recording"]["chunk_duration"]
        self.silence_threshold = config["recording"]["silence_threshold"]
        self.data_dir = get_data_dir(config)
        self.running = True

    def _get_audio_dir(self) -> Path:
        today = datetime.now().strftime("%Y-%m-%d")
        audio_dir = self.data_dir / "audio" / today
        audio_dir.mkdir(parents=True, exist_ok=True)
        return audio_dir

    def _is_silent(self, audio: np.ndarray) -> bool:
        rms = np.sqrt(np.mean(audio.astype(np.float64) ** 2))
        return rms < self.silence_threshold

    def _record_loop(self, stream: sd.InputStream):
        samples_per_chunk = self.sample_rate * self.chunk_duration
        buffer = []
        collected = 0

        while self.running:
            # Read in 1-second blocks
            data, overflowed = stream.read(self.sample_rate)
            if overflowed:
                logger.warning("Audio buffer overflow — some audio may be lost")

            buffer.append(data.copy())
            collected += len(data)

            if collected >= samples_per_chunk:
                audio = np.concatenate(buffer, axis=0)[:samples_per_chunk]
                buffer = []
                collected = 0

                if self._is_silent(audio):
                    logger.debug("Silence detected, skipping chunk")
                    continue

                timestamp = datetime.now().strftime("%H-%M-%S")
                audio_dir = self._get_audio_dir()
                wav_path = audio_dir / f"{timestamp}.wav"

                wavfile.write(str(wav_path), self.sample_rate, audio)
                logger.info(f"Recorded chunk: {wav_path.name}")
                self.transcript_queue.put(str(wav_path))

    def run(self):
        logger.info("Recorder starting — listening on default mic")
        while self.running:
            try:
                with sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype="int16",
                    blocksize=self.sample_rate,
                ) as stream:
                    self._record_loop(stream)
            except sd.PortAudioError as e:
                logger.warning(f"Mic error: {e}. Retrying in 5s...")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Recorder error: {e}. Retrying in 5s...")
                time.sleep(5)

    def stop(self):
        self.running = False
