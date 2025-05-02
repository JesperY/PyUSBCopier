import os
import shutil
from typing import List, Set
from .config import config
from .logger import logger

class USBCopier:
    """USB copier class"""
    def __init__(self):
        self.stop_flag = False
    
    def do_copy(self, drive: str) -> bool:
        """Execute copy operation"""
        try:
            # Get whitelist configuration
            white_list = config.white_list
            
            # Create destination directory
            backup_dir = os.path.join(config.backup_dst, os.path.basename(drive))
            os.makedirs(backup_dir, exist_ok=True)
            
            logger.info(f"Starting to copy files from {drive} to {backup_dir}")
            # Copy files
            self._copy_files(drive, backup_dir, white_list)
            logger.info(f"Copy completed: {drive} -> {backup_dir}")
            return True
        except Exception as e:
            logger.error(f"Copy failed: {e}")
            return False
        finally:
            self.stop_flag = False
    
    def _copy_files(self, src_dir: str, dst_dir: str, white_list: dict):
        """Recursively copy files"""
        for root, dirs, files in os.walk(src_dir):
            if self.stop_flag:
                logger.info("Copy operation stopped")
                break
            
            # Check if directory name is in whitelist
            rel_path = os.path.relpath(root, src_dir)
            if rel_path != '.':
                dir_parts = rel_path.split(os.sep)
                if not any(part in white_list['dirname'] for part in dir_parts):
                    continue
            
            # Create destination directory
            dst_root = os.path.join(dst_dir, rel_path)
            os.makedirs(dst_root, exist_ok=True)
            
            # Copy files
            for file in files:
                if self.stop_flag:
                    logger.info("Copy operation stopped")
                    break
                
                # Check if filename and extension are in whitelist
                filename = os.path.basename(file)
                file_ext = os.path.splitext(file)[1].lower()
                
                if (filename in white_list['filename'] or 
                    file_ext in white_list['suffix']):
                    src_file = os.path.join(root, file)
                    dst_file = os.path.join(dst_root, file)
                    
                    try:
                        shutil.copy2(src_file, dst_file)
                        logger.debug(f"Copied: {src_file} -> {dst_file}")
                    except Exception as e:
                        logger.error(f"Failed to copy file {src_file}: {e}") 