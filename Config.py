import getpass

import yaml


class Config:
    _data = []

    KEEPASS_YAML_PATH = "KeePass"
    TFS_YAML_PATH = "TFS"

    def __init__(self):
        print("Config:")
        with open("config.yaml") as stream:
            try:
                self._data = yaml.safe_load(stream)
                print(self._data)
            except yaml.YAMLError as exc:
                print(exc)

    def get_keepass_path(self) -> str:
        return self._data[self.KEEPASS_YAML_PATH]["path"]

    def get_keepass_password(self) -> str:
        result = self._data[self.KEEPASS_YAML_PATH]["password"]
        if result is not None:
            return result

        return getpass.getpass("Keepass Password: ")

    def get_tfs_token_path(self) -> str:
        return self._data[self.TFS_YAML_PATH]["KeePassEntry"]

    def get_tfs_organization(self):
        return self._data[self.TFS_YAML_PATH]["organization"]

    def get_tfs_baseUrl(self):
        return self._data[self.TFS_YAML_PATH]["baseUrl"]

    def get_tfs_repo(self):
        return self._data[self.TFS_YAML_PATH]["repo"]

    def get_tfs_project(self):
        return self._data[self.TFS_YAML_PATH]["project"]

