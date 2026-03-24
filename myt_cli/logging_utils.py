import logging
from pathlib import Path
from typing import List

from myt_cli.config import LoggingConfig


def configure_logging(config: LoggingConfig) -> None:
    log_path = Path(config.file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handlers: List[logging.Handler] = [
        logging.StreamHandler(),
        logging.FileHandler(log_path, encoding="utf-8"),
    ]
    logging.basicConfig(
        level=getattr(logging, config.level, logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=handlers,
        force=True,
    )
