#!/usr/bin/env python

import sys

from flume.config import Config
from flume.discoverer import Discoverer, DiscovererOptions


def main(args=None):
    options = DiscovererOptions()
    args = options.parse_args(args)
    # Read the config file
    config = Config(args)
    discoverer = Discoverer(config, args)
    discoverer.start()


if __name__ == "__main__":
    main(sys.argv[1:])
