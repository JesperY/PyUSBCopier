import wmi
import logging
from typing import Set
import time
import os
import win32com.client

# Ensure log directory exists
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'usb_monitor.log')),
        logging.StreamHandler()
    ]
)

class USBMonitor:
    def __init__(self):
        """Initialize USB monitor"""
        self.wmi_obj = wmi.WMI()
        self.last_usb_drives: Set[str] = set()
        logging.info("USB monitor initialized")
        
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
            logging.error(f"Failed to get USB drive list: {str(e)}")
            return set()

    def detect_usb_change(self, current_drives: Set[str]) -> str:
        """Detect USB storage device changes"""
        removed = self.last_usb_drives - current_drives
        added = current_drives - self.last_usb_drives
        
        if removed:
            logging.info(f"USB drive(s) removed: {removed}")
            return f'USB drive(s) removed: {", ".join(removed)}'
        elif added:
            logging.info(f"USB drive(s) inserted: {added}")
            return f'USB drive(s) inserted: {", ".join(added)}'
        return ''

    def monitor(self) -> None:
        """Monitor USB storage devices"""
        logging.info("Starting USB drive monitoring...")
        print("Monitoring USB drives. Messages will be displayed when USB storage devices are connected or disconnected...")
        
        # Initialize device list
        self.last_usb_drives = self.get_usb_drives()
        logging.info(f"Initial USB drives: {self.last_usb_drives}")
        
        try:
            while True:
                current_drives = self.get_usb_drives()
                message = self.detect_usb_change(current_drives)
                
                if message:
                    print(message)
                    logging.info(message)
                
                self.last_usb_drives = current_drives
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("Monitoring stopped")
            logging.info("User interrupted, stopping monitoring")

def main():
    logging.info("Program started")
    monitor = USBMonitor()
    try:
        monitor.monitor()
    except Exception as e:
        logging.error(f"Program error: {str(e)}")
    finally:
        logging.info("Program ended")
        
if __name__ == '__main__':
    main()