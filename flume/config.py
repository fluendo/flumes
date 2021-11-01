import configparser
import os

from sqlalchemy.engine import URL, make_url


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
            if args.driver:
                self.config["Database"]["driver"] = args.driver
            if args.user:
                self.config["Database"]["user"] = args.user
            if args.password:
                self.config["Database"]["password"] = args.password
            if args.host:
                self.config["Database"]["host"] = args.host
            if args.port:
                self.config["Database"]["port"] = args.port
            if args.database:
                self.config["Database"]["database"] = args.database

        # Generate the other parameters based on the uri
        if "uri" in self.config["Database"]:
            url = make_url(self.config["Database"]["uri"])
            if not "driver" in self.config["Database"] and url.drivername:
                self.config["Database"]["driver"] = url.drivername
            if not "user" in self.config["Database"] and url.username:
                self.config["Database"]["user"] = url.username
            if not "password" in self.config["Database"] and url.password:
                self.config["Database"]["password"] = url.password
            if not "host" in self.config["Database"] and url.host:
                self.config["Database"]["host"] = url.host
            if not "port" in self.config["Database"] and url.port:
                self.config["Database"]["port"] = url.port
            if not "database" in self.config["Database"] and url.database:
                self.config["Database"]["database"] = url.database

        # Generate the uri based on the other parameters
        url = URL(
            self.config["Database"]["driver"],
            username=self.config["Database"].get("user", None),
            password=self.config["Database"].get("password", None),
            host=self.config["Database"].get("host", None),
            port=self.config["Database"].get("port", None),
            database=self.config["Database"].get("database", None),
        )
        self.config["Database"]["uri"] = str(url)

        print(url)
        if not "uri" in self.config["Database"]:
            raise ConfigError("Missing database uri")
        if not "dir" in self.config["Media"]:
            raise ConfigError("Missing media directory")

    def get_media_files_directory(self):
        return self.config["Media"]["dir"]

    def get_database_uri(self):
        return self.config["Database"]["uri"]

    def get_database_diriver(self):
        return self.config["Database"]["driver"]

    def get_database_user(self):
        return self.config["Database"]["user"]

    def get_database_password(self):
        return self.config["Database"]["password"]

    def get_database_host(self):
        return self.config["Database"]["host"]

    def get_database_port(self):
        return self.config["Database"]["port"]

    def get_database_database(self):
        return self.config["Database"]["database"]
