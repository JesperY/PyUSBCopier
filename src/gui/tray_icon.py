from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QMessageBox, QApplication
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, QObject, pyqtSignal
import os

from .icons import get_icon, get_resource_path
from .config_editor import ConfigEditorGUI
from ..core.logger import logger

class TrayIcon(QObject):
    """System tray icon manager class"""
    # Define signals
    monitor_toggled = pyqtSignal(bool)  # True=start monitoring, False=stop monitoring
    copy_stopped = pyqtSignal()  # Stop copy signal
    app_exit = pyqtSignal()  # Exit application signal
    autostart_toggled = pyqtSignal(bool)  # True=enable autostart, False=disable autostart
    
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.config_editor = None
        
        # Ensure system supports tray icons
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.error("System does not support system tray icons")
            return
            
        # Create system tray icon
        try:
            # Get icon path and check if file exists
            icon_path = get_resource_path('icon.ico')
            logger.info(f"Attempting to load icon: {icon_path}")
            
            # Create icon directly from file
            if os.path.exists(icon_path):
                logger.info(f"Icon file exists, loading: {icon_path}")
                icon = QIcon(icon_path)
                
                # Check if icon is empty
                if icon.isNull():
                    logger.error("Loaded icon is empty, trying backup icon")
                    # Try to load PNG icon
                    png_path = get_resource_path('icon.png')
                    if os.path.exists(png_path):
                        logger.info(f"Attempting to load PNG icon: {png_path}")
                        icon = QIcon(png_path)
            else:
                logger.error(f"Icon file does not exist: {icon_path}")
                # Try to use built-in icon
                icon = QIcon.fromTheme("application-x-executable")
                if icon.isNull():
                    # If built-in icon is also unavailable, use default system icon
                    logger.warning("Using system default icon")
                    icon = QIcon.fromTheme("application")
            
            # Create system tray icon
            self.tray_icon = QSystemTrayIcon(self.app)
            
            # Set icon
            if not icon.isNull():
                self.tray_icon.setIcon(icon)
                logger.info("Successfully set tray icon")
            else:
                logger.error("Cannot create valid icon")
            
            # Create menu
            self.tray_menu = QMenu()
            
            # Status display
            self.status_action = QAction("Status: Monitoring")
            self.status_action.setEnabled(False)
            self.tray_menu.addAction(self.status_action)
            
            # Copy status display
            self.copy_status_action = QAction("Copy: Idle")
            self.copy_status_action.setEnabled(False)
            self.tray_menu.addAction(self.copy_status_action)
            
            # Add separator
            self.tray_menu.addSeparator()
            
            # Stop/Start monitoring action
            self.toggle_monitor_action = QAction("Stop Monitoring")
            self.toggle_monitor_action.triggered.connect(self.toggle_monitor)
            self.tray_menu.addAction(self.toggle_monitor_action)
            
            # Stop current copy action
            self.stop_copy_action = QAction("Stop Copy")
            self.stop_copy_action.triggered.connect(self.stop_current_copy)
            self.stop_copy_action.setEnabled(False)  # Initially disabled
            self.tray_menu.addAction(self.stop_copy_action)
            
            # Edit configuration action
            self.edit_config_action = QAction("Edit Configuration")
            self.edit_config_action.triggered.connect(self.open_config_editor)
            self.tray_menu.addAction(self.edit_config_action)
            
            # Autostart option
            self.autostart_action = QAction("Start with Windows")
            self.autostart_action.setCheckable(True)
            self.autostart_action.triggered.connect(self.toggle_autostart)
            self.tray_menu.addAction(self.autostart_action)
            
            # Add separator
            self.tray_menu.addSeparator()
            
            # Exit action
            self.exit_action = QAction("Exit")
            self.exit_action.triggered.connect(self.exit_app)
            self.tray_menu.addAction(self.exit_action)
            
            # Set tray icon menu
            self.tray_icon.setContextMenu(self.tray_menu)
            self.tray_icon.setToolTip("USB Backup Tool")
            
            # Connect signals and slots
            self.tray_icon.activated.connect(self.icon_activated)
            
            # Show icon - this step is important
            self.tray_icon.show()
            logger.info("System tray icon initialized")
        except Exception as e:
            logger.error(f"Error creating system tray icon: {e}")
    
    def show_notification(self, title: str, message: str, icon=QSystemTrayIcon.MessageIcon.Information, duration=5000):
        """Show a system notification
        
        Args:
            title (str): Notification title
            message (str): Notification message
            icon: Icon type (Information, Warning, Critical)
            duration (int): Display duration in milliseconds
        """
        try:
            # Check if system supports messages
            if self.tray_icon.supportsMessages():
                self.tray_icon.showMessage(title, message, icon, duration)
                logger.info(f"Showing notification: {title} - {message}")
            else:
                logger.warning("System does not support tray notifications")
        except Exception as e:
            logger.error(f"Failed to show notification: {e}")
            
    def toggle_monitor(self):
        """Toggle monitoring status"""
        is_monitoring = self.status_action.text() == "Status: Monitoring"
        self.monitor_toggled.emit(not is_monitoring)
    
    def toggle_autostart(self):
        """Toggle autostart setting"""
        enable = self.autostart_action.isChecked()
        logger.info(f"{'Enabling' if enable else 'Disabling'} autostart")
        self.autostart_toggled.emit(enable)
    
    def update_autostart_status(self, is_enabled: bool):
        """Update autostart menu item status"""
        self.autostart_action.setChecked(is_enabled)
        logger.info(f"Autostart status updated: {'enabled' if is_enabled else 'disabled'}")
    
    def stop_current_copy(self):
        """Stop current copy operation"""
        self.copy_stopped.emit()
    
    def open_config_editor(self):
        """Open configuration editor"""
        if not self.config_editor:
            self.config_editor = ConfigEditorGUI()
            self.config_editor.setWindowFlags(self.config_editor.windowFlags() & ~Qt.WindowType.WindowMinimizeButtonHint)
        
        # If window is closed, recreate it
        if not self.config_editor.isVisible():
            self.config_editor = ConfigEditorGUI()
        
        # Show and activate window
        self.config_editor.show()
        self.config_editor.activateWindow()
        self.config_editor.raise_()  # Ensure window is on top
    
    def icon_activated(self, reason):
        """Handle tray icon activation event"""
        logger.info(f"Tray icon activated, reason: {reason}")
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.open_config_editor()
    
    def exit_app(self):
        """Exit application"""
        reply = QMessageBox.question(
            None, 
            'Confirm Exit', 
            'Are you sure you want to exit USB Backup Tool?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.app_exit.emit()
    
    def update_status(self, is_monitoring: bool):
        """Update monitoring status display"""
        if is_monitoring:
            self.status_action.setText("Status: Monitoring")
            self.toggle_monitor_action.setText("Stop Monitoring")
        else:
            self.status_action.setText("Status: Stopped")
            self.toggle_monitor_action.setText("Start Monitoring")
    
    def update_copy_status(self, is_copying: bool):
        """Update copy status display"""
        if is_copying:
            self.copy_status_action.setText("Copy: In Progress")
            self.stop_copy_action.setEnabled(True)
        else:
            self.copy_status_action.setText("Copy: Idle")
            self.stop_copy_action.setEnabled(False) 