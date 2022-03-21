from flumes.config import Config
from flumes.discoverer import Discoverer, DiscovererOptions

#################################
####### Discoverer Setup ########
#################################


def discoverer_setup():
    options = DiscovererOptions()
    args = options.parse_args(["-i", "sqlite:///flumes-test.db", "-d", "tests/samples"])
    config = Config(args)
    return Discoverer(config, args)
