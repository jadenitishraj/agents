import os
import logging
import logging_loki

def get_loki_logger(name="research"):
    LOKI_URL = os.getenv("LOKI_URL", "").rstrip("/") + "/loki/api/v1/push"
    LOKI_USER_ID = os.getenv("LOKI_USER_ID")
    LOKI_API_KEY = os.getenv("LOKI_API_KEY")

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid adding handler multiple times if reloaded
    if not logger.handlers:
        logging.basicConfig(level=logging.INFO)
        if LOKI_URL and LOKI_USER_ID and LOKI_API_KEY:
            loki_handler = logging_loki.LokiHandler(
                url=LOKI_URL, 
                tags={"application": "research-agents"},
                auth=(LOKI_USER_ID, LOKI_API_KEY),
                version="1",
            )
            logger.addHandler(loki_handler)
    return logger

logger = get_loki_logger()
