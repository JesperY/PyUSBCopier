import os
import yaml
import platform
import sys
from typing import Dict, List, Any
from .logger import logger

class Config:
    """Configuration management class"""
    def __init__(self):
        # Set application name
        self.app_name = "USBBackup"
        
        # Determine user config directory based on OS
        self.config_dir = self.get_config_directory()
        
        # Configuration file path
        self.config_file = os.path.join(self.config_dir, 'config.yaml')
        
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Default config
        self.default_config = {
            'backup_dst': os.path.join(os.path.expanduser('~'), 'USBBackup'),
            'white_list': {
                'dirname': [],
                'filename': [],
                'suffix': []
            }
        }

        # Load config file
        self.config = self.load_config()
        
        # Log config location
        logger.info(f"Using configuration file: {self.config_file}")
    
    def get_config_directory(self) -> str:
        """Get the appropriate configuration directory based on the OS"""
        home = os.path.expanduser('~')
        system = platform.system()
        
        if system == 'Windows':
            # Windows: %APPDATA%\USBBackup or %USERPROFILE%\AppData\Roaming\USBBackup
            app_data = os.environ.get('APPDATA')
            if not app_data:
                app_data = os.path.join(home, 'AppData', 'Roaming')
            return os.path.join(app_data, self.app_name)
        
        elif system == 'Darwin':
            # macOS: ~/Library/Application Support/USBBackup
            return os.path.join(home, 'Library', 'Application Support', self.app_name)
        
        else:
            # Linux/Unix: ~/.config/usb-backup
            xdg_config_home = os.environ.get('XDG_CONFIG_HOME')
            if not xdg_config_home:
                xdg_config_home = os.path.join(home, '.config')
            return os.path.join(xdg_config_home, self.app_name.lower())
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration file

        Returns:
            Dict[str, Any]: Configuration data
        """
        # Check if config file exists
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = yaml.safe_load(f)
                    if loaded_config is None:
                        logger.warning("Config file is empty, using default config")
                        return self.default_config.copy()
                    logger.info(f"Configuration loaded from {self.config_file}")
                    return loaded_config
            except Exception as e:
                logger.error(f"Failed to load configuration file: {e}")
                return self.default_config.copy()
        else:
            # If file doesn't exist, create it with default config
            logger.info("Configuration file not found, creating default")
            self.save_config(self.default_config.copy())
            return self.default_config.copy()
    
    def save_config(self, config_data: Dict[str, Any]) -> bool:
        """Save configuration to file
        
        Args:
            config_data (Dict[str, Any]): Configuration data

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, allow_unicode=True)
            self.config = config_data # update config
            logger.info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save configuration file: {e}")
            return False
    
    def write_default(self) -> bool:
        """Write default configuration

        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("Writing default configuration")
        return self.save_config(self.default_config.copy())
    
    def reload(self) -> None:
        """Reload configuration"""
        logger.info("Reloading configuration")
        self.config = self.load_config()
    
    @property
    def backup_dst(self) -> str:
        """Get backup destination path"""
        return self.config.get('backup_dst', self.default_config['backup_dst'])
    
    @property
    def white_list(self) -> Dict[str, List[str]]:
        """Get whitelist configuration"""
        return self.config.get('white_list', self.default_config['white_list'])

# Create global configuration instance
config = Config() 