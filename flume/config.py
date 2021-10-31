import configparser
import os


class ConfigError(Exception):
    pass


class Config(object):
    SYSTEM_CONFIG = "/etc/flume"

    def __init__(self, args=None):
        user_configuration = "{}/{}".format(os.getenv("HOME"), ".flume")
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

        # override now with passed in arguments
        if not "Database" in self.config:
            self.config["Database"] = {}
        if not "Media" in self.config:
            self.config["Media"] = {}

        if args:
            if args.dir:
                self.config["Media"]["dir"] = args.dir
            if args.uri:
                self.config["Database"]["uri"] = args.uri
            if args.user:
                self.config["Database"]["user"] = args.user
            if args.password:
                self.config["Database"]["password"] = args.password

        if not "uri" in self.config["Database"]:
            raise ConfigError("Missing database uri")
        if not "user" in self.config["Database"]:
            raise ConfigError("Missing database user")
        if not "password" in self.config["Database"]:
            raise ConfigError("Missing database password")
        if not "dir" in self.config["Media"]:
            raise ConfigError("Missing media directory")

    def get_media_files_directory(self):
        return self.config["Media"]["dir"]

    def get_database_uri(self):
        return self.config["Database"]["uri"]

    def get_database_user(self):
        return self.config["Database"]["user"]

    def get_database_password(self):
        return self.config["Database"]["password"]
