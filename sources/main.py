import logging
import logging.config
from datetime import datetime
from pathlib import Path

from LIFT import Process as LiftProcess
from logging_config import CONFIG


def setup_logging(log_dir=Path("logs")):
    # Create logs directory
    log_dir.mkdir(parents=True, exist_ok=True)

    # Generate log filename if not provided
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_name = f"LIFT_{timestamp}.log"
    _log_file = log_dir / log_file_name

    # Apply configuration
    logging.config.dictConfig(CONFIG(_log_file))

    # Create logger for this module and log setup completion
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - File: {_log_file}")
    logger.debug(f"File log level: DEBUG, Console log level: INFO")


def main():
    # setup folders
    lift_root = Path(".").resolve()
    if not lift_root.is_dir():
        raise EnvironmentError(f"LIFT directory not found at {lift_root.absolute()}")

    input_dir = (lift_root / "input").resolve()
    if not input_dir.is_dir():
        raise EnvironmentError(f"Input directory not found at {input_dir.absolute()}")

    env_file = (input_dir / ".env").resolve()
    if not env_file.is_file():
        raise EnvironmentError(f"Environment file not found at {env_file.absolute()}")

    # setup logging
    log_dir = (lift_root / ".logs").resolve()
    setup_logging(log_dir)

    # start LIFT
    LiftProcess(lift_root, input_dir, env_file).run()


if __name__ == "__main__":
    main()
