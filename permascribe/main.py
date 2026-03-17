import logging
import queue
import sys
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import load_config, get_data_dir
from .recorder import Recorder
from .transcriber import Transcriber
from .summarizer import Summarizer
from .web import create_app


def setup_logging(data_dir: Path):
    data_dir.mkdir(parents=True, exist_ok=True)
    log_path = data_dir / "permascribe.log"

    handlers = [
        RotatingFileHandler(log_path, maxBytes=10_000_000, backupCount=5),
        logging.StreamHandler(sys.stdout),
    ]

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )


def main():
    config = load_config()
    data_dir = get_data_dir(config)
    setup_logging(data_dir)

    logger = logging.getLogger("permascribe")
    logger.info("PermaScribe starting up")

    transcript_queue = queue.Queue()

    recorder = Recorder(config, transcript_queue)
    transcriber = Transcriber(config, transcript_queue)
    summarizer = Summarizer(config)
    app = create_app(config, summarizer)

    # Start worker threads
    threading.Thread(target=recorder.run, daemon=True, name="recorder").start()
    logger.info("Recorder thread started")

    threading.Thread(target=transcriber.run, daemon=True, name="transcriber").start()
    logger.info("Transcriber thread started")

    threading.Thread(target=summarizer.run_scheduler, daemon=True, name="summarizer").start()
    logger.info("Summarizer scheduler started")

    # Flask on main thread
    logger.info(f"Web UI at http://{config['web']['host']}:{config['web']['port']}")
    app.run(
        host=config["web"]["host"],
        port=config["web"]["port"],
        debug=False,
        use_reloader=False,
    )


if __name__ == "__main__":
    main()
