# ey-ay/config/logging_config.py -- can we rename this just into logging.py?

import logging
import logging.handlers
import sys
from pathlib import Path
from config.settings import LoggingConfig, AppConfig


class ColoredFormatter(logging.Formatter):
    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record):
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
            )

        return super().format(record)


def setup_logging(
    name: str = None, log_file: str = None, level: str = None, use_colors: bool = True
):
    # Get or create logger
    logger = logging.getLogger(name)

    # Don't add handlers if they already exist
    if logger.handlers:
        return logger

    # Set level
    log_level = getattr(logging, level or LoggingConfig.LEVEL)
    logger.setLevel(log_level)

    # Prevent propagation to avoid duplicate logs
    logger.propagate = False

    # Create formatters
    file_formatter = logging.Formatter(
        LoggingConfig.FILE_FORMAT, datefmt=LoggingConfig.DATE_FORMAT
    )

    if use_colors:
        console_formatter = ColoredFormatter(
            LoggingConfig.CONSOLE_FORMAT, datefmt=LoggingConfig.DATE_FORMAT
        )
    else:
        console_formatter = logging.Formatter(
            LoggingConfig.CONSOLE_FORMAT, datefmt=LoggingConfig.DATE_FORMAT
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler with rotation
    if log_file is None:
        log_file = AppConfig.LOGS_DIR / LoggingConfig.FILE
    else:
        log_file = Path(log_file)

    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Rotating file handler (10MB max, keep 5 backups)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"  # 10MB
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    return setup_logging(name)


# Example usage decorator
def log_execution_time(func):
    import time
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            logger.debug(f"{func.__name__} executed in {execution_time:.2f}ms")
            return result

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(
                f"{func.__name__} failed after {execution_time:.2f}ms: {e}",
                exc_info=True,
            )
            raise

    return wrapper


if __name__ == "__main__":
    # Test logging setup
    logger = get_logger(__name__)

    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

    print("\nLogging setup test complete!")
    print(f"Logs written to: {AppConfig.LOGS_DIR}")
