import logging

from pluggle.settings import LOG_DIR


def setup_logging(debug: bool = False) -> None:
    """Configure the `pluggle` logger hierarchy.

    The console handler always stays at INFO, so normal runs show phase
    progress without detail. Debug mode additionally writes DEBUG-level
    output to a file. Existing handlers are cleared on each call, making
    the function safe to invoke more than once.

    Args:
        debug: Whether to enable file-based DEBUG logging.
    """
    root_logger = logging.getLogger("pluggle")
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)
    root_logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root_logger.addHandler(console_handler)

    if debug:
        file_handler = logging.FileHandler(
            LOG_DIR / "pluggle_debug.log", encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        root_logger.addHandler(file_handler)
