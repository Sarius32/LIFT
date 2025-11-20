import logging
import logging.config
from datetime import datetime
from pathlib import Path

CONFIG = lambda console_lvl, file_lvl, file_path: {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s | %(name)-20s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s',
        },
        'simple': {
            'format': '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s'
        },
        'minimal': {
            'format': '%(levelname)s: %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': console_lvl,
            'formatter': 'simple',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': file_lvl,
            'formatter': 'detailed',
            'filename': str(file_path),
            'mode': 'a',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'encoding': 'utf-8'
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console', 'file']
    },
    'loggers': {
        # Silence httpx access logs (like HTTP Request: ...)
        'httpx': {
            'level': 'WARNING',  # show only warnings and above
            'propagate': False
        },
        'httpcore': {
            'level': 'WARNING',
            'propagate': False
        }
    }
}

_setup = False


def _setup_logging(
        log_level_file="DEBUG",
        log_level_console="INFO",
        log_file=None,
        timestamp=None,
        log_dir="logs",
        app_name="LIFT"
):
    global _setup

    if not _setup:
        # Create logs directory
        log_path_obj = Path(log_dir)
        log_path_obj.mkdir(exist_ok=True)

        # Generate log filename if not provided
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if log_file is None:
            log_file = f"{app_name}_{timestamp}.log"

        log_file_path = log_path_obj / log_file

        # Apply configuration
        logging.config.dictConfig(CONFIG(log_level_console, log_level_file, log_file_path))

        # Create logger for this module and log setup completion
        logger = logging.getLogger(__name__)
        logger.info(f"Logging initialized - File: {log_file_path}")
        logger.debug(f"File log level: {log_level_file}, Console log level: {log_level_console}")

        _setup = True


_setup_logging()


def get_logger(name):
    return logging.getLogger(name)
