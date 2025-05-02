#!/usr/bin/env python
"""
USB Backup Tool - Main Entry Point
This script serves as the entry point for the USB Backup application.
"""
import sys
import os
import logging
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import QObject, pyqtSignal
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
        
        # Create system tray icon
        self.tray_icon = TrayIcon(self.app)
        
        # Connect signals
        self.tray_icon.monitor_toggled.connect(self.toggle_monitor)
        self.tray_icon.copy_stopped.connect(self.stop_current_copy)
        self.tray_icon.app_exit.connect(self.exit_app)
        
        logger.info("Application initialization complete")
    
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

def main():
    """Application entry point"""
    try:
        logger.info("USB Backup Tool starting")
        app_instance = USBBackupApp()
        # Ensure object is not garbage collected
        sys.exit(app_instance.run())
    except Exception as e:
        logger.error(f"Application failed to start: {e}", exc_info=True)
        if 'app' in locals():
            sys.exit(app.exec())
        else:
            sys.exit(1)

if __name__ == "__main__":
    main() 