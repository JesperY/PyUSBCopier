import sys
import os
import threading
import time
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, QObject, pyqtSignal

from GUI import ConfigEditorGUI
from usb_monitor import USBMonitor
from logger import logger

class USBBackupApp(QObject):
    # 定义信号，用于线程间通信
    monitor_stopped_signal = pyqtSignal()
    copy_status_changed_signal = pyqtSignal(bool)  # True=复制中，False=没有复制
    
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
            self.tray_icon.setIcon(self.app.style().standardIcon(self.app.style().StandardPixmap.SP_ComputerIcon))
        else:
            self.tray_icon.setIcon(QIcon(icon_path))
        
        # 创建菜单
        self.tray_menu = QMenu()
        
        # 状态显示
        self.status_action = QAction("状态: 监控中")
        self.status_action.setEnabled(False)
        self.tray_menu.addAction(self.status_action)
        
        # 复制状态显示
        self.copy_status_action = QAction("复制: 空闲")
        self.copy_status_action.setEnabled(False)
        self.tray_menu.addAction(self.copy_status_action)
        
        # 添加分隔线
        self.tray_menu.addSeparator()
        
        # 停止/启动监控 动作
        self.toggle_monitor_action = QAction("停止监控")
        self.toggle_monitor_action.triggered.connect(self.toggle_monitor)
        self.tray_menu.addAction(self.toggle_monitor_action)
        
        # 停止当前复制 动作
        self.stop_copy_action = QAction("停止复制")
        self.stop_copy_action.triggered.connect(self.stop_current_copy)
        self.stop_copy_action.setEnabled(False)  # 初始禁用
        self.tray_menu.addAction(self.stop_copy_action)
        
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
        self.tray_icon.setToolTip("USB备份工具")
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.icon_activated)
        
        # 初始化配置编辑器
        self.config_editor = None
        
        # 初始化监控器和监控线程
        self.monitor = USBMonitor()
        # 重要: 设置中断标志以允许立即停止复制
        self.monitor.copier.stop_flag = False
        
        self.monitor_thread = None
        self.monitoring = False
        self.copying = False
        
        # 连接信号
        self.monitor_stopped_signal.connect(self.on_monitor_stopped)
        self.copy_status_changed_signal.connect(self.on_copy_status_changed)
        
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
            # 同时停止所有复制操作
            self.stop_current_copy()
            logger.info("正在停止USB监控...")
    
    def stop_current_copy(self):
        """立即停止当前正在进行的复制操作"""
        if hasattr(self.monitor.copier, 'stop_flag'):
            self.monitor.copier.stop_flag = True
            logger.info("已发送停止复制信号")
            self.tray_icon.showMessage("USB备份工具", "正在停止复制操作，请稍候...", 
                                      QSystemTrayIcon.MessageIcon.Information, 1500)
    
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
                            
                            # 设置复制状态为活跃
                            self.monitor.copier.stop_flag = False
                            self.copying = True
                            self.copy_status_changed_signal.emit(True)
                            
                            # 执行复制
                            copy_result = self.monitor.copier.do_copy(drive)
                            
                            # 复制完成后，更新状态
                            self.copying = False
                            self.copy_status_changed_signal.emit(False)
                            
                            # 如果是因为停止标志而中断，通知用户
                            if self.monitor.copier.stop_flag:
                                self.tray_icon.showMessage("USB备份工具", 
                                                         f"驱动器 {drive} 的复制操作已中止，可以安全移除设备", 
                                                         QSystemTrayIcon.MessageIcon.Information, 3000)
                            elif copy_result:
                                self.tray_icon.showMessage("USB备份工具", 
                                                         f"驱动器 {drive} 的复制操作已完成", 
                                                         QSystemTrayIcon.MessageIcon.Information, 3000)
                
                self.monitor.last_usb_drives = current_drives
                
                # 减少CPU使用率并提高响应性
                for i in range(10):
                    if not self.monitoring:
                        break
                    time.sleep(0.1)
        except Exception as e:
            logger.error(f"监控线程错误: {str(e)}")
        finally:
            logger.info("监控线程已停止")
            self.copying = False
            self.copy_status_changed_signal.emit(False)
            self.monitor_stopped_signal.emit()
    
    def on_monitor_stopped(self):
        """监控线程停止后的处理"""
        self.status_action.setText("状态: 已停止")
        self.toggle_monitor_action.setText("启动监控")
        logger.info("USB监控已停止")
        self.tray_icon.showMessage("USB备份工具", "USB监控已停止", QSystemTrayIcon.MessageIcon.Information, 2000)
    
    def on_copy_status_changed(self, is_copying):
        """复制状态变更处理"""
        self.copying = is_copying
        if is_copying:
            self.copy_status_action.setText("复制: 正在进行")
            self.stop_copy_action.setEnabled(True)
        else:
            self.copy_status_action.setText("复制: 空闲")
            self.stop_copy_action.setEnabled(False)
    
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
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(1.0)
            QApplication.quit()
    
    def run(self):
        """运行应用程序"""
        self.tray_icon.showMessage(
            "USB备份工具", 
            "应用程序已在后台启动，将自动监控USB设备插入", 
            QSystemTrayIcon.MessageIcon.Information, 
            3000
        )
        
        return self.app.exec()

# FIXME 当前正在复制的文件过大时，停止复制所需时间太长
# TODO 优化代码，Mointor 类可以去掉
if __name__ == "__main__":
    app = USBBackupApp()
    sys.exit(app.run())