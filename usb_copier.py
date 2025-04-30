# @Time: 2025/04/25
# @Author: Junpo Yu
# @Email: junpo_yu@163.com

import os
import shutil
from logger import logger
from Config import config
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
            # logger.debug("check dirname: " + os.path.basename(source_path))
            if os.path.dirname(source_path) in config.white_list.dirname:
                logger.debug(f"Path {source_path} is in whitelist, skipping.")
                return True
        else:
            
            # 检查文件名
            if config.white_list.get('filename'):
                # logger.debug("check filename: " + os.path.splitext(os.path.basename(source_path))[0])
                if os.path.splitext(os.path.basename(source_path))[0] in config.white_list.get('filename'):
                    logger.debug(f"Path {source_path} is in whitelist, skipping.")
                    return True
            # 检查后缀名
            if config.white_list.get('suffix'):
                # logger.debug("check suffix: " + os.path.splitext(os.path.basename(source_path))[-1])
                if os.path.splitext(source_path)[-1] in config.white_list.get('suffix'):
                    logger.debug(f"Path {source_path} is in whitelist, skipping.")
                    return True
        return False
    
    def is_new_file(self, source_path: str, dst_path: str) -> bool:
        """
        Check if the source path is a new file
        
        Args:
            source_path (str): source path need to be checked

        Returns:
            bool: True if the source path is a new file, False otherwise
        """
        if os.path.isfile(source_path):
            if os.path.isfile(dst_path):
                return os.path.getmtime(source_path) > os.path.getmtime(dst_path)
        return True

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
        # 首先检查停止标志
        if self.stop_flag:
            logger.info(f"复制操作被用户中止: {src}")
            return False
            
        if self.is_white_list(src):
            logger.info(f"Path {src} is in whitelist, skipping.")
            return True
        if not self.is_new_file(src, dst):
            logger.info(f"Path {src} is not a new version, skipping.")
            return True
        
        try:
            if os.path.isdir(src):
                os.makedirs(dst, exist_ok=True)
                for item in os.listdir(src):
                    # 每项文件前都检查停止标志
                    if self.stop_flag:
                        logger.info(f"复制操作被用户中止: {src}")
                        return False
                    
                    s = os.path.join(src, item)
                    d = os.path.join(dst, item)
                    result = self.copy_with_filter(s, d, symlinks)
                    if result is False:  # 如果子任务被中止
                        return False
            else:
                # 复制大文件前再次检查停止标志
                if self.stop_flag:
                    logger.info(f"复制操作被用户中止: {src}")
                    return False
                    
                # 对于大文件，可以考虑分块复制并在每块之间检查停止标志
                # 但简单起见，这里使用直接复制
                shutil.copy2(src, dst)
                logger.info(f"Copied file: {src} -> {dst}")
            return True
        except Exception as e:
            logger.error(f"复制文件失败: {src} -> {dst}: {str(e)}")
            return False

    def do_copy(self, source) -> bool:
        """
        do copy

        Args:
            source (str): source path need to be copied

        Returns:
            bool: Success for True and False for otherwise
        """
        # 重置停止标志
        self.stop_flag = False
        
        try:
            drive = os.path.splitdrive(source)[0]+'\\'
            unique_id = self.get_volume_serial(drive)
            if not unique_id:
                logger.error(f"Failed to get unique id for {drive}")
                return False
                
            dst = os.path.join(config.backup_dst, unique_id)
            logger.info(f"Start copying from {source} to {dst}")

            result = self.copy_with_filter(source, dst)
            
            if result is False:
                logger.info(f"复制操作被用户中止: {source}")
                return False
                
            logger.info("复制操作成功完成")
            return True
        except Exception as e:
            logger.error(f"复制操作失败: {str(e)}", exc_info=True)
            return False
