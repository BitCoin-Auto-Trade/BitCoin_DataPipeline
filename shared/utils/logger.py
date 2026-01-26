import sys
from loguru import logger

logger.remove()


def setup_logger(service: str):
    logger.add(sys.stdout, colorize=True,
               format="<green>{time:HH:mm:ss}</green> | <cyan>{extra[name]: <8}</cyan> | <level>{level: <8}</level> | <level>{message}</level>",
               level="INFO")

    logger.add(f"logs/{service}.log", rotation="50 MB", retention="7 days", compression="zip",
               format="{time:YYYY-MM-DD HH:mm:ss} | {extra[name]: <8} | {level: <8} | {message}",
               level="INFO")


def get_logger(name: str):
    return logger.bind(name=name)
