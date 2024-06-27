from pykeepass import PyKeePass
from Config import Config


class KeePass:
    _db: PyKeePass = None
    _config: Config = None
    
    def __init__(self, config: Config):
        self._config = config
        self._db = PyKeePass(config.get_keepass_path(), password=config.get_keepass_password())
        
    def get_tfs_token(self) -> str:
        return self._db.find_entries(title=self._config.get_tfs_token_path(), first=True).password

    def get_tfs_username(self) -> str:
        return self._db.find_entries(title=self._config.get_tfs_token_path(), first=True).username
