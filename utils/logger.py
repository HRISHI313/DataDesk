# utils/logger.py

import logging
import os
from datetime import datetime

def setup_logger():
    
    # create logs folder if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Log Rotator: Keep only the 15 most recent log files
    try:
        log_files = []
        for f in os.listdir("logs"):
            if f.startswith("datadesk_") and f.endswith(".txt"):
                path = os.path.join("logs", f)
                log_files.append((path, os.path.getmtime(path)))
        
        # Sort files by modification time (ascending)
        log_files.sort(key=lambda x: x[1])
        
        # Keep at most 14 existing files to leave room for the new one (total 15)
        max_existing = 14
        if len(log_files) > max_existing:
            num_to_delete = len(log_files) - max_existing
            for i in range(num_to_delete):
                file_to_delete = log_files[i][0]
                try:
                    os.remove(file_to_delete)
                except Exception:
                    pass
    except Exception:
        pass
        
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