from flume import __version__
from flume.config import Config
from flume.discoverer import Discoverer, DiscovererOptions


def test_version():
    assert __version__ == "0.1.0"


def test_discovery():
    # Create an sqlite based dicovery with the media at samples dir
    options = DiscovererOptions()
    args = options.parse_args(
        [
            "-i",
            "sqlite:///flume.db",
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
    discoverer = Discoverer(config, args)
    discoverer.start()
    # Check the correct information is stored in the database
