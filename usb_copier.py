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

    # TODO 备份白名单：盘符/盘名 目录名 文件名 后缀名
    def is_white_list(self, source_path: str) -> bool:
        # print(source_path)
        return False
    

    def get_volume_serial(self, drive_letter):
        """
        获取指定盘符的卷序列号（Volume Serial Number），可作为USB设备的唯一标识符。

        Args:
            drive_letter (str): 盘符字符串，如 'E:\\'

        Returns:
            str or None: 卷序列号（8位大写十六进制字符串），获取失败时返回 None
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
        递归复制 src 目录下的所有内容到 dst 目录下。
        可在 check_white_list 中实现白名单过滤。

        Args:
            src (str): 源路径
            dst (str): 目标路径
            symlinks (bool): 是否保留符号链接
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
