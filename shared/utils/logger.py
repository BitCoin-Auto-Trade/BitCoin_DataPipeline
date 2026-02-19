import sys
import os
import requests
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK")


def slack_handler(message):
    """Custom handler to send error logs to Slack."""
    payload = {
        "text": f"🚨 *BitCoin Data Pipeline Error*\n\n```{message}```"
    }
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=5)
        response.raise_for_status()
    except Exception as e:
        # Avoid infinite recursion if slack notification itself fails
        sys.stderr.write(f"Failed to send Slack notification: {e}\n")


logger.remove()


def setup_logger(service: str):
    logger.add(sys.stdout, colorize=True,
               format="<green>{time:HH:mm:ss}</green> | <cyan>{extra[name]: <8}</cyan> | <level>{level: <8}</level> | <level>{message}</level>",
               level="INFO")

    logger.add(f"logs/{service}.log", rotation="50 MB", retention="7 days", compression="zip",
               format="{time:YYYY-MM-DD HH:mm:ss} | {extra[name]: <8} | {level: <8} | {message}",
               level="INFO")

    if SLACK_WEBHOOK_URL:
        logger.add(slack_handler, level="ERROR", format="{time:YYYY-MM-DD HH:mm:ss} | {extra[name]: <8} | {level: <8} | {message}")


def get_logger(name: str):
    return logger.bind(name=name)
