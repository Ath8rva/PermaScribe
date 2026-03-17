import logging
from datetime import datetime
from pathlib import Path

import markdown
import requests
from flask import Flask, jsonify, render_template, redirect, url_for

from .config import get_data_dir

logger = logging.getLogger(__name__)


def create_app(config: dict, summarizer=None) -> Flask:
    app = Flask(__name__, template_folder=str(Path(__file__).parent.parent / "templates"))
    data_dir = get_data_dir(config)

    def _read_summary(date_str: str) -> str | None:
        path = data_dir / "summaries" / f"{date_str}.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    def _list_summary_dates() -> list[str]:
        summary_dir = data_dir / "summaries"
        if not summary_dir.exists():
            return []
        dates = sorted(
            [f.stem for f in summary_dir.glob("*.md")],
            reverse=True,
        )
        return dates

    def _count_transcripts(date_str: str) -> int:
        transcript_dir = data_dir / "transcripts" / date_str
        if not transcript_dir.exists():
            return 0
        return len(list(transcript_dir.glob("*.txt")))

    def _read_transcripts(date_str: str) -> list[dict]:
        transcript_dir = data_dir / "transcripts" / date_str
        if not transcript_dir.exists():
            return []
        result = []
        for f in sorted(transcript_dir.glob("*.txt")):
            result.append({
                "time": f.stem.replace("-", ":"),
                "content": f.read_text(encoding="utf-8").strip(),
            })
        return result

    @app.route("/")
    def index():
        today = datetime.now().strftime("%Y-%m-%d")
        summary_md = _read_summary(today)
        summary_html = markdown.markdown(summary_md) if summary_md else None
        transcript_count = _count_transcripts(today)
        return render_template(
            "index.html",
            date=today,
            summary_html=summary_html,
            transcript_count=transcript_count,
            dates=_list_summary_dates()[:10],
        )

    @app.route("/day/<date_str>")
    def day(date_str: str):
        summary_md = _read_summary(date_str)
        summary_html = markdown.markdown(summary_md) if summary_md else None
        transcript_count = _count_transcripts(date_str)
        return render_template(
            "index.html",
            date=date_str,
            summary_html=summary_html,
            transcript_count=transcript_count,
            dates=_list_summary_dates()[:10],
        )

    @app.route("/history")
    def history():
        dates = _list_summary_dates()
        entries = []
        for d in dates:
            entries.append({
                "date": d,
                "transcript_count": _count_transcripts(d),
            })
        return render_template("history.html", entries=entries)

    @app.route("/transcripts/<date_str>")
    def transcripts(date_str: str):
        items = _read_transcripts(date_str)
        return render_template(
            "history.html",
            entries=None,
            transcripts=items,
            transcript_date=date_str,
        )

    @app.route("/summarize", methods=["POST"])
    def trigger_summarize():
        if summarizer is None:
            return jsonify({"error": "Summarizer not available"}), 503
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            summary = summarizer.summarize_day(today)
            if summary:
                from .emailer import send_summary
                send_summary(config, today, summary)
                return redirect(url_for("index"))
            return jsonify({"error": "No transcripts found for today"}), 404
        except Exception as e:
            logger.error(f"Manual summarization failed: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/status")
    def status():
        # Check Ollama
        ollama_ok = False
        try:
            r = requests.get(f"{config['summarization']['ollama_url']}/api/tags", timeout=5)
            ollama_ok = r.ok
        except Exception:
            pass

        today = datetime.now().strftime("%Y-%m-%d")
        transcript_dir = data_dir / "transcripts" / today
        last_transcript = None
        if transcript_dir.exists():
            files = sorted(transcript_dir.glob("*.txt"))
            if files:
                last_transcript = files[-1].stem.replace("-", ":")

        return jsonify({
            "recording": True,
            "date": today,
            "transcript_count": _count_transcripts(today),
            "last_transcript": last_transcript,
            "ollama_reachable": ollama_ok,
            "summary_exists": _read_summary(today) is not None,
        })

    return app
