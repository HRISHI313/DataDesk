# utils/logger.py

import logging
import os
from datetime import datetime

def setup_logger():
    
    # create logs folder if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # create a new log file for each session with timestamp
    log_filename = f"logs/datadesk_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    logging.basicConfig(
        filename  = log_filename,
        level     = logging.INFO,
        format    = "%(asctime)s — %(levelname)s — %(module)s — %(message)s",
        datefmt   = "%Y-%m-%d %H:%M:%S",
        encoding  = "utf-8"
    )
    
    logger = logging.getLogger("datadesk")
    logger.info(f"Logger initialized successfully")
    
    return logger