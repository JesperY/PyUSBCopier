import os
import yaml
import threading

class Config:
    _lock = threading.Lock()
    _config_path = 'config.yaml'
    _default_config = {
        "backup_dst": "backup"
    }

    def __init__(self) -> None:
        self.reload()

    def reload(self):
        with self._lock:
            if not os.path.exists(self._config_path):
                with open(self._config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(self._default_config, f, allow_unicode=True)
                self._config_data = self._default_config
            else:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    self._config_data = yaml.safe_load(f) or self._default_config
    
    @property
    def backup_dst(self):
        return self._config_data.get('backup_dst', self._default_config['backup_dst'])  

config = Config()