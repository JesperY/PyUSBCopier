# @Time: 2025/04/25
# @Author: Junpo Yu
# @Email: junpo_yu@163.com

import os
import shutil
from logger import logger
from config import config
import ctypes


class USBcopier:
    def __init__(self) -> None:
        pass

    def is_white_list(self, source_path: str) -> bool:
        """
        Check if the source path is in the white list

        Args:
            source_path (str): source path need to be checked

        Returns:
            bool: True if the source path is in the white list, False otherwise
        """
        # 检查目录名
        if os.path.isdir(source_path) and config.white_list.get('dirname'):
            logger.debug("check dirname: " + os.path.basename(source_path))
            if os.path.dirname(source_path) in config.white_list.dirname:
                return True
        else:
            
            # 检查文件名
            if config.white_list.get('filename'):
                logger.debug("check filename: " + os.path.splitext(os.path.basename(source_path))[0])
                if os.path.splitext(os.path.basename(source_path))[0] in config.white_list.get('filename'):
                    return True
            # 检查后缀名
            if config.white_list.get('suffix'):
                logger.debug("check suffix: " + os.path.splitext(os.path.basename(source_path))[-1])
                if os.path.splitext(source_path)[-1] in config.white_list.get('suffix'):
                    return True
        return False
    

    def get_volume_serial(self, drive_letter):
        """
        Get the volume serial number of the specified drive letter (Volume Serial Number), which can be used as the unique identifier of the USB device.

        Args:
            drive_letter (str): drive letter string, e.g. 'E:\\'

        Returns:
            str or None: volume serial number (8-digit uppercase hexadecimal string), return None if failed
        """
        # drive_letter: 'E:\\'
        volume_name_buf = ctypes.create_unicode_buffer(1024)
        fs_name_buf = ctypes.create_unicode_buffer(1024)
        serial_number = ctypes.c_ulong()
        max_component_length = ctypes.c_ulong()
        file_system_flags = ctypes.c_ulong()
        ret = ctypes.windll.kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(drive_letter),
            volume_name_buf,
            ctypes.sizeof(volume_name_buf),
            ctypes.byref(serial_number),
            ctypes.byref(max_component_length),
            ctypes.byref(file_system_flags),
            fs_name_buf,
            ctypes.sizeof(fs_name_buf)
        )
        if ret:
            return f"{serial_number.value:08X}"
        else:
            return None
        

    def copy_with_filter(self, src, dst, symlinks=False):
        """
        Recursively copy all contents of src directory to dst directory.

        Args:
            src (str): source path
            dst (str): destination path
            symlinks (bool): whether to preserve symlinks
        """
        if self.is_white_list(src):
            logger.info(f"Path {src} is in whitelist, skipping.")
            return
        
        if os.path.isdir(src):
            os.makedirs(dst, exist_ok=True)
            for item in os.listdir(src):
                s = os.path.join(src, item)
                d = os.path.join(dst, item)
                self.copy_with_filter(s, d, symlinks)
        else:
            shutil.copy2(src, dst)
            logger.info(f"Copied file: {src} -> {dst}")

    # 执行备份操作
    # TODO 按需备份
    # TODO 优化git开发流程
    def do_copy(self, source) -> bool:
        """
        do copy

        Args:
            source (str): source path need to be copied

        Returns:
            bool: Success for True and False for otherwise
        """
        try:
            drive = os.path.splitdrive(source)[0]+'\\'
            unique_id = self.get_volume_serial(drive)
            if not unique_id:
                # TODO 无法获取卷序列号时使用其他方法
                logger.error(f"Failed to get unique id for {drive}")
            dst = os.path.join(config.backup_dst, unique_id)
            logger.info("Start copying from {source} to {dst}")

            self.copy_with_filter(source, dst)
            logger.info("Copy operation completed successfully")
            return True
        except Exception as e:
            logger.error(f"Copy operation failed: {str(e)}", exc_info=True)
            return False


    # 
