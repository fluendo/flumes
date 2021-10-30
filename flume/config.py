import configparser
import os


class ConfigError(Exception):
    pass


class Config(object):
    SYSTEM_CONFIG = "/etc/flu-config"

    def __init__(self, args=None):
        user_configuration = "{}/{}".format(os.getenv("HOME"), ".flu-config")
        self.config = configparser.ConfigParser()
        # try with the passed in configuration, if any
        if args and args.config:
            self.config.read(args.config)
        # try with the system wide configuration
        elif os.path.isfile(Config.SYSTEM_CONFIG):
            self.config.read(Config.SYSTEM_CONFIG)
        # try with the local user configuration
        elif os.path.isfile(user_configuration):
            self.config.read(user_configuration)
        else:
            raise ConfigError("Missing configuration file")

    def get_media_files_directory(self):
        return self.config["Media"]["dir"]

    def get_database_uri(self):
        return self.config["Database"]["uri"]

    def get_database_user(self):
        return self.config["Database"]["user"]

    def get_database_password(self):
        return self.config["Database"]["password"]
