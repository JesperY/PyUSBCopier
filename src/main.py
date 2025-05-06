#!/usr/bin/env python
"""
USB Backup Tool - Main Entry Point
This script serves as the entry point for the USB Backup application.
"""
import sys
import os
import logging
import socket
import tempfile
import ctypes
import winreg
from PyQt6.QtWidgets import QApplication, QWidget, QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon


# Add the src directory to the path if it's not already there
if os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) not in sys.path:
    sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import modules - trying relative imports first, then falling back to absolute imports
try:
    from .gui.tray_icon import TrayIcon
    from .core.monitor import USBMonitor
    from .core.usb_copier import USBCopier
    from .core.config import Config
    from .gui.icons import get_icon, get_resource_path
    from .core.config import Config
except ImportError:
    from src.gui.tray_icon import TrayIcon
    from src.core.monitor import USBMonitor
    from src.core.usb_copier import USBCopier
    from src.core.config import Config
    from src.gui.icons import get_icon, get_resource_path
    from src.core.logger import logger

class AutoStartManager:
    """Manages application autostart functionality"""
    def __init__(self, app_name="USB Backup Tool"):
        self.app_name = app_name
        self.registry_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    def set_autostart(self, enable=True):
        """Enable or disable autostart
        
        Args:
            enable (bool): True to enable autostart, False to disable
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get executable path
            executable = sys.executable
            
            # If running from a frozen executable (PyInstaller)
            if getattr(sys, 'frozen', False):
                executable = os.path.abspath(sys.executable)
            # If running from a Python script
            else:
                script_path = os.path.abspath(sys.argv[0])
                executable = f'"{executable}" "{script_path}"'
            
            # Open registry key
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key, 0, 
                               winreg.KEY_SET_VALUE) as registry_key:
                
                if enable:
                    # Add to startup
                    winreg.SetValueEx(registry_key, self.app_name, 0, winreg.REG_SZ, executable)
                    logger.info(f"Added {self.app_name} to autostart with command: {executable}")
                else:
                    # Remove from startup if exists
                    try:
                        winreg.DeleteValue(registry_key, self.app_name)
                        logger.info(f"Removed {self.app_name} from autostart")
                    except FileNotFoundError:
                        # Key doesn't exist, nothing to remove
                        logger.info(f"{self.app_name} was not in autostart")
            
            return True
        except Exception as e:
            logger.error(f"Failed to {'enable' if enable else 'disable'} autostart: {e}")
            return False
    
    def is_autostart_enabled(self):
        """Check if autostart is enabled
        
        Returns:
            bool: True if enabled, False otherwise
        """
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key, 0,
                               winreg.KEY_READ) as registry_key:
                try:
                    winreg.QueryValueEx(registry_key, self.app_name)
                    return True
                except FileNotFoundError:
                    return False
        except Exception as e:
            logger.error(f"Failed to check autostart status: {e}")
            return False

class SingleInstanceChecker:
    """Class to ensure only one instance of the application runs at a time"""
    def __init__(self, unique_id="usb_backup_app_lock"):
        self.unique_id = unique_id
        self.mutex_name = f'Global\\{unique_id}'
        self.socket = None
        self.port = 45678  # Arbitrary port for socket-based lock
    
    def is_running_windows(self):
        """Check if another instance is running using Windows mutex"""
        try:
            # Try to create a named mutex
            mutex = ctypes.windll.kernel32.CreateMutexW(None, False, self.mutex_name)
            last_error = ctypes.windll.kernel32.GetLastError()
            
            # ERROR_ALREADY_EXISTS indicates another instance is running
            if last_error == 183:  # ERROR_ALREADY_EXISTS
                if mutex:
                    ctypes.windll.kernel32.CloseHandle(mutex)
                return True
            return False
        except Exception as e:
            logger.error(f"Error checking for running instance (Windows): {e}")
            return False
    
    def is_running_socket(self):
        """Check if another instance is running using socket binding"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind(('localhost', self.port))
            self.socket.listen(1)
            return False
        except socket.error:
            return True
    
    def is_running(self):
        """Check if another instance of the application is running"""
        if sys.platform == 'win32':
            return self.is_running_windows()
        else:
            return self.is_running_socket()
    
    def cleanup(self):
        """Clean up resources"""
        if self.socket:
            self.socket.close()

class USBBackupApp(QObject):
    """USB backup application main class"""
    def __init__(self):
        super().__init__()
        
        logger.info("Starting USB Backup Tool")
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"Python path: {sys.path}")
        
        # Check sys.argv before creating QApplication instance
        if not QApplication.instance():
            # If no application instance exists, create one
            self.app = QApplication(sys.argv)
        else:
            # If it already exists, use it
            self.app = QApplication.instance()
        
        # Create an invisible main window as parent for tray icon to prevent garbage collection
        self.dummy_widget = QWidget()
        
        # Set application icon
        try:
            # Try to load icon
            icon_path = get_resource_path('icon.ico')
            if os.path.exists(icon_path):
                app_icon = QIcon(icon_path)
                if not app_icon.isNull():
                    self.app.setWindowIcon(app_icon)
                    self.dummy_widget.setWindowIcon(app_icon)
                    logger.info(f"Set application icon: {icon_path}")
                else:
                    logger.error(f"Loaded icon is empty: {icon_path}")
                    # Try PNG icon
                    png_path = get_resource_path('icon.png')
                    if os.path.exists(png_path):
                        app_icon = QIcon(png_path)
                        if not app_icon.isNull():
                            self.app.setWindowIcon(app_icon)
                            self.dummy_widget.setWindowIcon(app_icon)
                            logger.info(f"Set application icon: {png_path}")
            else:
                logger.warning(f"Icon file not found: {icon_path}")
        except Exception as e:
            logger.error(f"Failed to set application icon: {e}")
        
        # Ensure application does not exit when last window is closed
        self.app.setQuitOnLastWindowClosed(False)
        
        self.dummy_widget.setGeometry(0, 0, 0, 0)  # Zero size window
        
        # Initialize components
        self.config = Config()
        self.usb_copier = USBCopier()
        self.monitor = USBMonitor()
        
        # Initialize autostart manager
        self.autostart_manager = AutoStartManager()
        
        # Create system tray icon
        self.tray_icon = TrayIcon(self.app)
        
        # Connect signals
        self.tray_icon.monitor_toggled.connect(self.toggle_monitor)
        self.tray_icon.copy_stopped.connect(self.stop_current_copy)
        self.tray_icon.app_exit.connect(self.exit_app)
        self.tray_icon.autostart_toggled.connect(self.set_autostart)
        
        # Initialize autostart status
        autostart_enabled = self.is_autostart_enabled()
        self.tray_icon.update_autostart_status(autostart_enabled)
        
        logger.info("Application initialization complete")
        
        # Show startup notification after a short delay
        QTimer.singleShot(500, self.show_startup_notification)
    
    def show_startup_notification(self):
        """Show startup notification"""
        self.tray_icon.show_notification(
            "USB Backup Tool",
            "USB Backup Tool is now running in the background.\nThe application will automatically backup USB devices when connected.",
            duration=8000
        )
    
    def toggle_monitor(self, start: bool):
        """Toggle monitoring status"""
        if start:
            self.monitor.start_monitor()
            self.tray_icon.update_status(True)
            logger.info("Monitoring started")
        else:
            self.monitor.stop_monitor()
            self.tray_icon.update_status(False)
            logger.info("Monitoring stopped")
    
    def stop_current_copy(self):
        """Stop current copy operation"""
        self.usb_copier.stop_current_copy()
        logger.info("Requested to stop current copy operation")
    
    def exit_app(self):
        """Exit application"""
        logger.info("Application is exiting")
        self.monitor.stop_monitor()
        self.app.quit()
    
    def run(self):
        """Run application"""
        # Start monitoring
        self.toggle_monitor(True)
        
        # Run application main loop
        logger.info("Application starting to run")
        return self.app.exec()
    
    def set_autostart(self, enable=True):
        """Set application to start automatically with Windows"""
        result = self.autostart_manager.set_autostart(enable)
        if result:
            self.tray_icon.show_notification(
                "Autostart Settings", 
                f"Application will {'start with Windows' if enable else 'not start with Windows'}.",
                duration=3000
            )
        return result
    
    def is_autostart_enabled(self):
        """Check if autostart is enabled"""
        return self.autostart_manager.is_autostart_enabled()

def show_already_running_message():
    """Show message that application is already running"""
    # Create a temporary QApplication if needed
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Set icon for the message box
    icon_path = get_resource_path('icon.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Show message
    QMessageBox.information(
        None, 
        "USB Backup Tool",
        "USB Backup Tool is already running.\nCheck your system tray for the icon.",
        QMessageBox.StandardButton.Ok
    )

def main():
    """Application entry point"""
    try:
        # Check if application is already running
        instance_checker = SingleInstanceChecker()
        if instance_checker.is_running():
            logger.info("Application is already running. Exiting.")
            show_already_running_message()
            return 0
        
        logger.info("USB Backup Tool starting")
        app_instance = USBBackupApp()
        # Ensure object is not garbage collected
        result = app_instance.run()
        
        # Clean up instance checker resources
        instance_checker.cleanup()
        
        return result
    except Exception as e:
        logger.error(f"Application failed to start: {e}", exc_info=True)
        if 'app' in locals():
            sys.exit(app.exec())
        else:
            sys.exit(1)

# TODO 配置文件保存到系统目录，更新版本后自动读取默认配置文件
# TODO 优化更新方式，能否在软件中自动拉取更新
# TODO 日志文件按日期保存
if __name__ == "__main__":
    sys.exit(main()) 