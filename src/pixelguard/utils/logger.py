import logging


class LoggerFactory:
    @staticmethod
    def create_logger(name):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    @staticmethod
    def setup_logging(level=logging.INFO, format=None):
        logging.basicConfig(
            level=level, format=format or "[%(levelname)s] %(name)s: %(message)s"
        )
