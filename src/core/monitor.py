import os
import threading
import time
from typing import List, Set
from .config import config
from .usb_copier import USBCopier
from .logger import logger

class USBMonitor:
    """USB device monitoring class"""
    def __init__(self):
        self.copier = USBCopier()
        self.last_usb_drives: Set[str] = set()
        self.monitoring = False
        self.monitor_thread = None
        logger.info("USB monitor initialization complete")
    
    def get_usb_drives(self) -> Set[str]:
        """Get all USB drives"""
        drives = set()
        for drive in range(ord('A'), ord('Z') + 1):
            drive_letter = chr(drive) + ':'
            if os.path.exists(drive_letter):
                # Check if it's a USB drive
                if self._is_usb_drive(drive_letter):
                    drives.add(drive_letter)
        return drives
    
    def _is_usb_drive(self, drive: str) -> bool:
        """Check if drive is a USB device"""
        try:
            # Get drive volume information
            import win32file
            import win32api
            drive_type = win32file.GetDriveType(drive)
            return drive_type == win32file.DRIVE_REMOVABLE
        except Exception as e:
            logger.error(f"Failed to check drive type: {e}")
            return False
    
    def detect_usb_change(self, current_drives: Set[str]) -> List[str]:
        """Detect USB device changes, return list of newly added drives"""
        added_drives = list(current_drives - self.last_usb_drives)
        if added_drives:
            logger.info(f"Detected new USB devices: {', '.join(added_drives)}")
        return added_drives
    
    def start_monitor(self):
        """Start monitoring"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logger.info("USB monitoring thread started")
    
    def stop_monitor(self):
        """Stop monitoring"""
        if self.monitoring:
            self.monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=1.0)
            logger.info("USB monitoring stopped")
    
    def _monitor_loop(self):
        """Monitoring loop"""
        self.last_usb_drives = self.get_usb_drives()
        logger.info(f"Initial USB devices: {', '.join(self.last_usb_drives) if self.last_usb_drives else 'none'}")
        
        while self.monitoring:
            current_drives = self.get_usb_drives()
            added_drives = self.detect_usb_change(current_drives)
            
            if added_drives:
                for drive in added_drives:
                    if self.monitoring:  # Check again in case monitoring stopped during copy
                        logger.info(f"Starting to process USB device: {drive}")
                        self.copier.do_copy(drive)
            
            self.last_usb_drives = current_drives
            
            # Reduce CPU usage
            for _ in range(10):
                if not self.monitoring:
                    break
                time.sleep(0.1)
    
    def stop_current_copy(self):
        """Stop current copy operation"""
        self.copier.stop_flag = True 
        logger.info("Copy stop flag set") 