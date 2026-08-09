import logging
import sys

from tqdm import tqdm

LOGGER_NAME = 'EduBatch'
LOG_FILE = 'app.log'


class TqdmLoggingHandler(logging.Handler):
    """Escreve no console via tqdm.write para não embaralhar a barra de progresso."""

    def emit(self, record):
        try:
            tqdm.write(self.format(record), file=sys.stderr)
        except Exception:
            self.handleError(record)


def setup_logging(log_file: str = LOG_FILE) -> logging.Logger:
    """Configura o logger da aplicação. Deve ser chamado uma vez, no início do programa."""
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(file_handler)

        console_handler = TqdmLoggingHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(console_handler)

    return logger


def get_logger() -> logging.Logger:
    return logging.getLogger(LOGGER_NAME)
