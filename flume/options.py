from argparse import ArgumentParser


class Options(ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        group = self.add_argument_group("configuration file")
        group.add_argument("-c", "--config", action="store", help="configuration file")
        group = self.add_argument_group("database")
        group.add_argument("-i", "--uri", action="store", help="database uri")
        group.add_argument("-e", "--drivername", action="store", help="database driver")
        group.add_argument("-u", "--user", action="store", help="database user name")
        group.add_argument(
            "-p", "--password", action="store", help="database user password"
        )
        group.add_argument("-o", "--host", action="store", help="database host")
        group.add_argument("-r", "--port", action="store", help="database port")
        group.add_argument("-b", "--database", action="store", help="database")
