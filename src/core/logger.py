import logging
import os
from datetime import datetime

def setup_logger():
    """Configure and return a logger"""
    # Create logger
    logger = logging.getLogger('USBBackup')
    logger.setLevel(logging.INFO)
    
    # Create log directory
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # Create file handler
    log_file = os.path.join(log_dir, f'usb_backup_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Create global logger instance
logger = setup_logger() 