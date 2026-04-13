# backend/logger.py

import os
import logging


def setup_logger():
    os.makedirs("logs", exist_ok=True)

    logger = logging.getLogger("rag_app")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        file_handler = logging.FileHandler("logs/app.log", encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger