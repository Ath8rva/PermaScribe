import logging
import os
import queue
from datetime import datetime
from pathlib import Path

from faster_whisper import WhisperModel

from .config import get_data_dir

logger = logging.getLogger(__name__)


class Transcriber:
    def __init__(self, config: dict, transcript_queue: queue.Queue):
        self.config = config
        self.transcript_queue = transcript_queue
        self.data_dir = get_data_dir(config)
        self.delete_audio = config["recording"]["delete_audio_after_transcription"]
        self.model = None

    def _load_model(self):
        tc = self.config["transcription"]
        model_size = tc["model"]
        device = tc["device"]
        if device == "auto":
            device = "cuda" if self._cuda_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"

        logger.info(f"Loading Whisper model '{model_size}' on {device} ({compute_type})")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        logger.info("Whisper model loaded")

    @staticmethod
    def _cuda_available() -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            try:
                import ctranslate2
                return "cuda" in ctranslate2.get_supported_compute_types("auto")
            except Exception:
                return False

    def _get_transcript_dir(self, date_str: str) -> Path:
        transcript_dir = self.data_dir / "transcripts" / date_str
        transcript_dir.mkdir(parents=True, exist_ok=True)
        return transcript_dir

    def _transcribe_file(self, wav_path: str):
        path = Path(wav_path)
        date_str = path.parent.name
        time_str = path.stem

        try:
            segments, info = self.model.transcribe(
                wav_path,
                language=self.config["transcription"]["language"],
                beam_size=5,
                vad_filter=True,
            )
            text = " ".join(seg.text.strip() for seg in segments)
        except Exception as e:
            logger.error(f"Transcription failed for {path.name}: {e}")
            return

        if not text.strip():
            logger.debug(f"Empty transcription for {path.name}, skipping")
            if self.delete_audio:
                self._safe_delete(path)
            return

        # Build timestamp header
        try:
            start_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H-%M-%S")
            chunk_dur = self.config["recording"]["chunk_duration"]
            end_seconds = start_time.second + chunk_dur
            end_minute = start_time.minute + end_seconds // 60
            end_second = end_seconds % 60
            end_hour = start_time.hour + end_minute // 60
            end_minute = end_minute % 60
            time_header = (
                f"[{start_time.strftime('%Y-%m-%d %H:%M:%S')} - "
                f"{end_hour:02d}:{end_minute:02d}:{end_second:02d}]"
            )
        except ValueError:
            time_header = f"[{date_str} {time_str}]"

        transcript_dir = self._get_transcript_dir(date_str)
        txt_path = transcript_dir / f"{time_str}.txt"
        txt_path.write_text(f"{time_header}\n{text}\n", encoding="utf-8")
        logger.info(f"Transcribed: {path.name} -> {txt_path.name} ({len(text)} chars)")

        if self.delete_audio:
            self._safe_delete(path)

    @staticmethod
    def _safe_delete(path: Path):
        try:
            os.remove(path)
        except OSError as e:
            logger.warning(f"Could not delete {path}: {e}")

    def run(self):
        self._load_model()
        logger.info("Transcriber ready — waiting for audio chunks")

        while True:
            try:
                wav_path = self.transcript_queue.get(timeout=5)
                self._transcribe_file(wav_path)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Transcriber error: {e}")
