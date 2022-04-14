import subprocess

import pytest

from flumes.config import Config
from flumes.discoverer import Discoverer, DiscovererOptions

#################################
####### Global Variables ########
#################################

db_name = "flumes-test.db"
db_rel_path = "tests/" + db_name
sqlite_command = "sqlite:///" + db_rel_path
file_path = "tests/samples/"
origin_file = "big-buck-bunny-480p-30sec.mp4"
destination_file = "sample-file.mp4"
modify_file = "sample-file2.mp4"
flumes_discoverer = (
    "python -m flumes.discoverer -d " + file_path + " -i " + sqlite_command
)


#################################
####### Discoverer Setup ########
#################################


# Set up a discoverer without iterations
@pytest.fixture
def discoverer():
    options = DiscovererOptions()
    args = options.parse_args(
        [
            "-i",
            sqlite_command,
            "-d",
            file_path,
        ]
    )
    config = Config(args)
    return Discoverer(config, args)


# Run the discoverer in a single iteration
def discoverer_run_once():
    options = DiscovererOptions()
    args = options.parse_args(["-i", sqlite_command, "-d", file_path, "-q"])
    config = Config(args)
    return Discoverer(config, args)


#################################
########### Database ############
#################################


# Returns the last available file id
def max_db_id():
    discoverer_test = discoverer_run_once()
    discoverer_test.start()
    db_select_result = subprocess.run(
        ["sqlite3", db_name, "select MAX(id) from files;"],
        capture_output=True,
        text=True,
        cwd="tests",
    )
    return db_select_result.stdout[:-1]
