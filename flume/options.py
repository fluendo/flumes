from argparse import ArgumentParser


class Options(ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        group = self.add_argument_group("configuration file")
        group.add_argument("-c", "--config", action="store", help="configuration file")
        group = self.add_argument_group("media files")
        group.add_argument(
            "-d", "--dir", action="store", help="media content directory"
        )
        group = self.add_argument_group("database")
        group.add_argument("-i", "--uri", action="store", help="database uri")
        group.add_argument("-u", "--user", action="store", help="database user name")
        group.add_argument(
            "-p", "--password", action="store", help="database user password"
        )
