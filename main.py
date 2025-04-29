import sys
import os
import threading
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, QObject, pyqtSignal

from GUI import ConfigEditorGUI
from usb_monitor import USBMonitor
from logger import logger

class USBBackupApp(QObject):
    # 定义信号，用于线程间通信
    monitor_stopped_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        # 确保应用程序不会随着最后一个窗口关闭而退出
        self.app.setQuitOnLastWindowClosed(False)
        
        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon()
        
        # 设置图标（您需要提供一个图标文件）
        icon_path = "icon.png"  # 替换为您的图标路径
        if not os.path.exists(icon_path):
            # 如果找不到图标，使用一个默认图标
            self.tray_icon.setIcon(self.app.style().standardIcon(self.app.style().StandardPixmap.SP_ComputerIcon))
        else:
            self.tray_icon.setIcon(QIcon(icon_path))
        
        # 创建菜单
        self.tray_menu = QMenu()
        
        # 状态显示
        self.status_action = QAction("状态: 监控中")
        self.status_action.setEnabled(False)
        self.tray_menu.addAction(self.status_action)
        
        # 添加分隔线
        self.tray_menu.addSeparator()
        
        # 停止/启动复制 动作
        self.toggle_monitor_action = QAction("停止监控")
        self.toggle_monitor_action.triggered.connect(self.toggle_monitor)
        self.tray_menu.addAction(self.toggle_monitor_action)
        
        # 编辑配置 动作
        self.edit_config_action = QAction("编辑配置")
        self.edit_config_action.triggered.connect(self.open_config_editor)
        self.tray_menu.addAction(self.edit_config_action)
        
        # 添加分隔线
        self.tray_menu.addSeparator()
        
        # 退出 动作
        self.exit_action = QAction("退出")
        self.exit_action.triggered.connect(self.exit_app)
        self.tray_menu.addAction(self.exit_action)
        
        # 设置托盘图标菜单
        self.tray_icon.setContextMenu(self.tray_menu)
        
        # 设置鼠标悬停时的提示文本
        self.tray_icon.setToolTip("USB备份工具")
        
        # 显示托盘图标
        self.tray_icon.show()
        
        # 连接托盘图标的激活信号
        self.tray_icon.activated.connect(self.icon_activated)
        
        # 初始化配置编辑器
        self.config_editor = None
        
        # 初始化监控器和监控线程
        self.monitor = USBMonitor()
        self.monitor_thread = None
        self.monitoring = False
        
        # 连接信号
        self.monitor_stopped_signal.connect(self.on_monitor_stopped)
        
        # 启动监控
        self.start_monitor()
        
    def start_monitor(self):
        """启动USB监控线程"""
        if not self.monitoring:
            self.monitor_thread = threading.Thread(target=self.run_monitor, daemon=True)
            self.monitoring = True
            self.monitor_thread.start()
            self.status_action.setText("状态: 监控中")
            self.toggle_monitor_action.setText("停止监控")
            logger.info("USB监控已启动")
            self.tray_icon.showMessage("USB备份工具", "USB监控已启动", QSystemTrayIcon.MessageIcon.Information, 2000)
    
    def stop_monitor(self):
        """停止USB监控线程"""
        if self.monitoring:
            self.monitoring = False
            # 发出信号通知监控线程停止
            logger.info("正在停止USB监控...")
            # monitor_thread会自行结束
    
    def run_monitor(self):
        """在单独的线程中运行监控"""
        try:
            logger.info("监控线程已启动")
            # 初始化设备列表
            self.monitor.last_usb_drives = self.monitor.get_usb_drives()
            
            while self.monitoring:
                current_drives = self.monitor.get_usb_drives()
                added_drives = self.monitor.detect_usb_change(current_drives)
                
                if added_drives:
                    for drive in added_drives:
                        if self.monitoring:  # 再次检查，以防在复制过程中停止
                            logger.info(f'复制驱动器: {drive}')
                            self.monitor.copier.do_copy(drive)
                
                self.monitor.last_usb_drives = current_drives
                # 减少CPU使用率
                for i in range(10):  # 分成10小段检查，以便更快响应停止命令
                    if not self.monitoring:
                        break
                    time.sleep(0.1)
        except Exception as e:
            logger.error(f"监控线程错误: {str(e)}")
        finally:
            logger.info("监控线程已停止")
            self.monitor_stopped_signal.emit()
    
    def on_monitor_stopped(self):
        """监控线程停止后的处理"""
        self.status_action.setText("状态: 已停止")
        self.toggle_monitor_action.setText("启动监控")
        logger.info("USB监控已停止")
        self.tray_icon.showMessage("USB备份工具", "USB监控已停止", QSystemTrayIcon.MessageIcon.Information, 2000)
    
    def toggle_monitor(self):
        """切换监控状态"""
        if self.monitoring:
            self.stop_monitor()
        else:
            self.start_monitor()
    
    def open_config_editor(self):
        """打开配置编辑器窗口"""
        if not self.config_editor:
            self.config_editor = ConfigEditorGUI()
            self.config_editor.setWindowFlags(self.config_editor.windowFlags() & ~Qt.WindowType.WindowMinimizeButtonHint)
        
        # 如果窗口已关闭，重新创建
        if not self.config_editor.isVisible():
            self.config_editor = ConfigEditorGUI()
        
        # 显示并激活窗口
        self.config_editor.show()
        self.config_editor.activateWindow()
    
    def icon_activated(self, reason):
        """处理托盘图标的激活事件"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.open_config_editor()
    
    def exit_app(self):
        """退出应用程序"""
        reply = QMessageBox.question(
            None, 
            '确认退出', 
            '确定要退出USB备份工具吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            logger.info("用户请求退出应用程序")
            self.stop_monitor()
            # 等待监控线程结束
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(1.0)  # 最多等待1秒
            QApplication.quit()
    
    def run(self):
        """运行应用程序"""
        # 显示启动通知
        self.tray_icon.showMessage(
            "USB备份工具", 
            "应用程序已在后台启动，将自动监控USB设备插入", 
            QSystemTrayIcon.MessageIcon.Information, 
            3000
        )
        
        return self.app.exec()

# 需要添加以下导入
import time

if __name__ == "__main__":
    app = USBBackupApp()
    sys.exit(app.run())