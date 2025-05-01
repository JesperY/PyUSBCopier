# @Time: 2025/04/27
# @Author: Junpo Yu
# @Email: junpo_yu@163.com

import wmi
import logger
from typing import Set
import time
import os
import win32com.client
from config import config
from logger import logger
from usb_copier import USBcopier

class USBMonitor:
    def __init__(self):
        """Initialize USB monitor"""
        self.wmi_obj = wmi.WMI()
        self.last_usb_drives: Set[str] = set()
        self.copier = USBcopier()
        
        logger.info("USB monitor initialized")
                
        
    def get_usb_drives(self) -> Set[str]:
        """Get all USB storage devices with drive letters"""
        try:
            drives = set()
            # Get all removable drives
            wmi_service = win32com.client.Dispatch("WbemScripting.SWbemLocator")
            wmi_obj = wmi_service.ConnectServer(".", "root\\cimv2")
            
            # Query for USB drives
            for drive in wmi_obj.ExecQuery("SELECT * FROM Win32_DiskDrive WHERE InterfaceType='USB'"):
                for partition in wmi_obj.ExecQuery(f"ASSOCIATORS OF {{Win32_DiskDrive.DeviceID='{drive.DeviceID}'}} WHERE AssocClass = Win32_DiskDriveToDiskPartition"):
                    for logical_disk in wmi_obj.ExecQuery(f"ASSOCIATORS OF {{Win32_DiskPartition.DeviceID='{partition.DeviceID}'}} WHERE AssocClass = Win32_LogicalDiskToPartition"):
                        drives.add(logical_disk.DeviceID)
            
            return drives
        except Exception as e:
            logger.error(f"Failed to get USB drive list: {str(e)}")
            return set()

    def detect_usb_change(self, current_drives: Set[str]) -> str:
        """Detect USB storage device changes"""
        removed = self.last_usb_drives - current_drives
        added = current_drives - self.last_usb_drives
        
        if removed:
            logger.info(f"USB drive(s) removed: {removed}")
            # return f'USB drive(s) removed: {", ".join(removed)}'
        elif added:
            logger.info(f"USB drive(s) inserted: {added}")
            # return f'USB drive(s) inserted: {", ".join(added)}'
        return added

    def monitor(self) -> None:
        """Monitor USB storage devices"""
        logger.info("Starting USB drive monitoring...")
        # print("Monitoring USB drives. Messages will be displayed when USB storage devices are connected or disconnected...")
        
        # Initialize device list
        self.last_usb_drives = self.get_usb_drives()
        logger.info(f"Initial USB drives: {self.last_usb_drives}")
        
        try:
            while True:
                current_drives = self.get_usb_drives()
                added_drives = self.detect_usb_change(current_drives)
                
                if added_drives:
                    for drive in added_drives:
                        logger.info(f'copying drive: {drive}')
                        self.copier.do_copy(drive)
                
                self.last_usb_drives = current_drives
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("User interrupted, stopping monitoring")

def main():
    # TODO 日志文件按日期分割，只保留最近七天
    logger.info("Program started")
    monitor = USBMonitor()
    try:
        monitor.monitor()
    except Exception as e:
        logger.error(f"Program error: {str(e)}")
    finally:
        logger.info("Program ended")
        
if __name__ == '__main__':
    main()