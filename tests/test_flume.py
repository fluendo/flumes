from flume import __version__
from flume.config import Config
from flume.discoverer import Discoverer, DiscovererOptions


def test_version():
    assert __version__ == "0.1.3"


def test_config():
    # Check URI has higher priority
    options = DiscovererOptions()
    args = options.parse_args(
        [
            "-i",
            "sqlite:///flume-test.db",
        ]
    )
    config = Config(args)
    assert config.get_database_database() == "flume-test.db"
    args = options.parse_args(
        [
            "-d",
            "tests/samples",
            "-u",
            "jl",
            "-p",
            "foo",
            "-q",
        ]
    )
    config = Config(args)
