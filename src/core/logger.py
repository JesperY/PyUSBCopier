import logging
import os
import platform
from datetime import datetime

def get_log_directory():
    """Get the appropriate log directory based on the OS"""
    home = os.path.expanduser('~')
    app_name = "USBBackup"
    system = platform.system()
    
    if system == 'Windows':
        # Windows: %LOCALAPPDATA%\USBBackup\Logs
        app_data = os.environ.get('LOCALAPPDATA')
        if not app_data:
            app_data = os.path.join(home, 'AppData', 'Local')
        return os.path.join(app_data, app_name, 'Logs')
    
    elif system == 'Darwin':
        # macOS: ~/Library/Logs/USBBackup
        return os.path.join(home, 'Library', 'Logs', app_name)
    
    else:
        # Linux/Unix: ~/.local/share/usb-backup/logs
        xdg_data_home = os.environ.get('XDG_DATA_HOME')
        if not xdg_data_home:
            xdg_data_home = os.path.join(home, '.local', 'share')
        return os.path.join(xdg_data_home, app_name.lower(), 'logs')

def setup_logger():
    """Configure and return a logger"""
    # Create logger
    logger = logging.getLogger('USBBackup')
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers (in case of reload)
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create log directory in user's directory
    log_dir = get_log_directory()
    os.makedirs(log_dir, exist_ok=True)
    
    # Create file handler with date in filename
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f'usb_backup_{date_str}.log')
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Log the log file location
    logger.info(f"Logging to file: {log_file}")
    
    return logger

# Create global logger instance
logger = setup_logger() 