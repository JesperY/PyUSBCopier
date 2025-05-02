import os
import yaml
from typing import Dict, List, Any
from .logger import logger

class Config:
    """Configuration management class"""
    def __init__(self):
        self.config_file = 'config/config.yaml' # path of config file
        # Ensure config directory exists
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True) # ensure the directory exists
        
        # default config
        self.default_config = {
            'backup_dst': os.path.join(os.path.expanduser('~'), 'USBBackup'),
            'white_list': {
                'dirname': [],
                'filename': [],
                'suffix': []
            }
        }

        # load config file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration file

        Returns:
            Dict[str, Any]: Configuration data
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.error(f"Failed to load configuration file: {e}")
                return self.default_config.copy()
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
            self.config = config_data # udpate config
            logger.info("Configuration saved successfully")
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