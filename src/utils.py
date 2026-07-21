import logging


def setup_logger() -> logging.Logger:
    """Configure and return the project logger.

    Returns:
        logging.Logger: Configured logger instance for the project.
    """
    logger = logging.getLogger(__name__)

    if not logger.handlers:
        logger.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
        )

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    return logger

logger = setup_logger()