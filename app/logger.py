import logging
import sys

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

def setup_logger():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))

    logging.basicConfig(
        level=logging.INFO, 
        handlers=[handler]
    )
    
    logger = logging.getLogger("ChatAPI")
    return logger

logger = setup_logger()