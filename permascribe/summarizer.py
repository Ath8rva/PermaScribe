import logging
import time
from datetime import datetime
from pathlib import Path

import requests
import schedule

from .config import get_data_dir

logger = logging.getLogger(__name__)

HOURLY_PROMPT = """You are summarizing a segment of continuous audio transcription from someone's day.
Time period: {start_time} to {end_time}

Extract the following from the transcript:
- Key topics discussed or thought about
- Any action items or to-dos mentioned
- Any decisions made
- Any notable quotes or important statements

Be concise but thorough. If the transcript is mostly casual/idle talk, note that briefly.

Transcript:
{transcript_text}"""

DAY_PROMPT = """You are creating an end-of-day summary from hourly summaries of a full day of audio transcription.
Date: {date}

Produce a well-structured markdown report with these sections:

## Day Overview
A 2-3 sentence overview of the day.

## Key Conversations & Topics
Bulleted list of main topics, conversations, and activities.

## Action Items / To-Dos
Numbered list of all tasks, action items, and to-dos identified throughout the day. Be specific.

## Key Decisions
Bulleted list of any decisions made or conclusions reached.

## Notable Quotes
Any important, memorable, or actionable statements worth remembering. Include approximate time.

## Mood & Energy
Brief note on overall tone/energy of the day if discernible.

---
Hourly Summaries:

{hourly_summaries}"""


class Summarizer:
    def __init__(self, config: dict):
        self.config = config
        self.data_dir = get_data_dir(config)
        self.ollama_url = config["summarization"]["ollama_url"]
        self.model = config["summarization"]["model"]
        self.hourly_chunk_minutes = config["summarization"]["hourly_chunk_minutes"]
        self.last_summary_date = None

    def _call_ollama(self, prompt: str, retries: int = 3) -> str | None:
        for attempt in range(retries):
            try:
                resp = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"num_ctx": 32768},
                    },
                    timeout=600,
                )
                resp.raise_for_status()
                return resp.json()["response"]
            except requests.RequestException as e:
                wait = 30 * (2 ** attempt)
                logger.warning(f"Ollama request failed (attempt {attempt + 1}/{retries}): {e}. Retrying in {wait}s")
                if attempt < retries - 1:
                    time.sleep(wait)
        logger.error("Ollama unreachable after all retries")
        return None

    def _load_transcripts(self, date_str: str) -> list[tuple[str, str]]:
        """Load all transcripts for a date, returns list of (filename, content)."""
        transcript_dir = self.data_dir / "transcripts" / date_str
        if not transcript_dir.exists():
            return []
        files = sorted(transcript_dir.glob("*.txt"))
        result = []
        for f in files:
            content = f.read_text(encoding="utf-8").strip()
            if content:
                result.append((f.stem, content))
        return result

    def _group_into_chunks(self, transcripts: list[tuple[str, str]]) -> list[dict]:
        """Group transcripts into hourly chunks."""
        if not transcripts:
            return []

        chunk_minutes = self.hourly_chunk_minutes
        chunks = []
        current_chunk = {"start": None, "end": None, "texts": []}

        for filename, content in transcripts:
            try:
                t = datetime.strptime(filename, "%H-%M-%S")
            except ValueError:
                current_chunk["texts"].append(content)
                continue

            if current_chunk["start"] is None:
                current_chunk["start"] = t

            # Check if we've exceeded the chunk duration
            if current_chunk["start"] is not None:
                elapsed = (t - current_chunk["start"]).total_seconds() / 60
                if elapsed >= chunk_minutes and current_chunk["texts"]:
                    current_chunk["end"] = t
                    chunks.append(current_chunk)
                    current_chunk = {"start": t, "end": None, "texts": []}

            current_chunk["texts"].append(content)
            current_chunk["end"] = t

        if current_chunk["texts"]:
            chunks.append(current_chunk)

        return chunks

    def summarize_day(self, date_str: str | None = None) -> str | None:
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")

        transcripts = self._load_transcripts(date_str)
        if not transcripts:
            logger.info(f"No transcripts found for {date_str}")
            return None

        logger.info(f"Summarizing {len(transcripts)} transcript chunks for {date_str}")

        chunks = self._group_into_chunks(transcripts)
        if not chunks:
            return None

        # Pass 1: Summarize each hourly chunk
        hourly_summaries = []
        for i, chunk in enumerate(chunks):
            start = chunk["start"].strftime("%H:%M") if chunk["start"] else "??:??"
            end = chunk["end"].strftime("%H:%M") if chunk["end"] else "??:??"
            combined_text = "\n\n".join(chunk["texts"])

            # Skip very short chunks (likely noise)
            if len(combined_text) < 50:
                continue

            prompt = HOURLY_PROMPT.format(
                start_time=start,
                end_time=end,
                transcript_text=combined_text,
            )

            logger.info(f"Summarizing chunk {i + 1}/{len(chunks)} ({start}-{end})")
            summary = self._call_ollama(prompt)
            if summary:
                hourly_summaries.append(f"### {start} - {end}\n{summary}")
            else:
                hourly_summaries.append(f"### {start} - {end}\n*Summary unavailable — Ollama error*")

        if not hourly_summaries:
            return None

        # Pass 2: Final day summary
        all_hourly = "\n\n".join(hourly_summaries)
        day_prompt = DAY_PROMPT.format(date=date_str, hourly_summaries=all_hourly)

        logger.info("Generating final day summary")
        day_summary = self._call_ollama(day_prompt)

        if not day_summary:
            # Fallback: save hourly summaries as the day summary
            day_summary = f"# Day Summary for {date_str}\n\n*Final summary generation failed. Hourly summaries below:*\n\n{all_hourly}"

        # Save summary
        summary_dir = self.data_dir / "summaries"
        summary_dir.mkdir(parents=True, exist_ok=True)
        summary_path = summary_dir / f"{date_str}.md"
        summary_path.write_text(day_summary, encoding="utf-8")
        logger.info(f"Day summary saved: {summary_path}")

        self.last_summary_date = date_str
        return day_summary

    def _scheduled_summarize(self):
        today = datetime.now().strftime("%Y-%m-%d")
        if self.last_summary_date == today:
            logger.info(f"Already summarized {today}, skipping")
            return
        summary = self.summarize_day(today)
        if summary:
            # Trigger email delivery
            from .emailer import send_summary
            send_summary(self.config, today, summary)

    def run_scheduler(self):
        trigger_time = self.config["summarization"]["trigger_time"]
        schedule.every().day.at(trigger_time).do(self._scheduled_summarize)
        logger.info(f"Summarizer scheduled at {trigger_time} daily")

        while True:
            schedule.run_pending()
            time.sleep(30)
