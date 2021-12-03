from flumes import __version__
from flumes.config import Config
from flumes.discoverer import Discoverer, DiscovererOptions


def test_version():
    assert __version__ == "0.1.7"


def test_config():
    # Check URI has higher priority
    options = DiscovererOptions()
    args = options.parse_args(
        [
            "-i",
            "sqlite:///flumes-test.db",
        ]
    )
    config = Config(args)
    assert config.get_database_database() == "flumes-test.db"
    args = options.parse_args(
        [
            "-e",
            "sqlite",
            "-u",
            "jl",
            "-p",
            "foo",
            "-b",
            "/",
            "-q",
        ]
    )
    config = Config(args)
    assert config.get_database_driver() == "sqlite"
    assert config.get_database_user() == "jl"
    assert config.get_database_password() == "foo"
    assert config.get_database_uri() == "sqlite://jl:foo@//"
