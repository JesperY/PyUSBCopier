# @Time: 2025/04/27
# @Author: Junpo Yu
# @Email: junpo_yu@163.com

import os
import logging

def setup_logger(name):
    """
    config logger

    Args:
        name (str): logger name

    Returns:
        logging.logger: instance of logger
    """

    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        file_handler = logging.FileHandler(
            os.path.join(log_dir, f'{name}.log'),
            encoding='utf-8'
        )

        console_handler = logging.StreamHandler()

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

logger = setup_logger("usb_copier")