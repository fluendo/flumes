import os
import shutil
import signal
import subprocess
import time

import pytest

from .conftest import *

#################################
######## Setup/Teardown #########
#################################


@pytest.fixture(scope="module")
def setup():
    try:
        os.remove(db_rel_path)
    except FileNotFoundError:
        print(
            "Database file {} could not be deleted because it wasn't found".format(
                db_rel_path
            )
        )
    yield


@pytest.fixture(scope="module")
def teardown():
    yield
    os.remove(db_rel_path)
    time.sleep(3)


# Global fixtures available to all tests within this module
pytestmark = pytest.mark.usefixtures("setup", "teardown")


# Content on usr1 signal function test
def test_on_usr1_signal(discoverer):
    setup
    # In case scanning is still in progress
    assert discoverer.signal_received == False
    assert discoverer.on_usr1_signal(signal.SIGUSR1) == None
    # Otherwise
    discoverer.numdirs = 0
    usr1 = discoverer.on_usr1_signal(signal.SIGUSR1)
    assert discoverer.signal_received == True
    assert usr1 == True
    discoverer.numdirs = 0
    discoverer.signal_received = False
    usr2 = discoverer.on_usr1_signal(signal.SIGUSR2)
    assert discoverer.signal_received == False
    assert usr2 == None
    teardown


# Copy media file to monitored path
def test_discover_newly_copied_file():
    # Setup
    setup
    discoverer_handle = discoverer_run_once()
    discoverer_handle.start()
    time.sleep(3)
    expected_file_db_id = int(get_max_id_db()) + 1
    # Test
    shutil.copy2(file_path + origin_file, file_path + destination_file)
    discoverer_handle = discoverer_run_once()
    discoverer_handle.start()
    time.sleep(3)
    db_select_result = subprocess.run(
        [
            "sqlite3",
            db_name,
            "select name from files where id={};".format(expected_file_db_id),
        ],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    db_select_result.check_returncode()
    assert db_select_result.stdout[:-1] == destination_file
    assert db_select_result.stderr == ""
    # Teardown
    os.remove(file_path + destination_file)
    teardown


# Delete media file from monitored path
def test_discover_removed_file():
    # Setup
    setup
    shutil.copy2(file_path + origin_file, file_path + destination_file)
    discoverer_handle = discoverer_run_once()
    discoverer_handle.start()
    time.sleep(3)
    assert int(get_max_id_db()) == 3
    assert int(get_num_entries_db()) == 3
    # Test
    os.remove(file_path + destination_file)
    time.sleep(3)
    discoverer_handle = discoverer_run_once()
    discoverer_handle.start()
    time.sleep(3)
    assert int(get_max_id_db()) == 2
    assert int(get_num_entries_db()) == 2
    # Teardown
    teardown


# Trigger manual rescan
def test_manual_rescan():
    # Setup
    setup
    shutil.copy2(file_path + origin_file, file_path + destination_file)
    process_handle = subprocess.Popen(flumes_discoverer, shell=True)
    time.sleep(3)
    os.rename(file_path + destination_file, file_path + modify_file)
    time.sleep(3)
    expected_file_db_id = int(get_max_id_db())
    # Test
    subprocess.run("kill -USR1 " + str(process_handle.pid), shell=True)
    time.sleep(3)
    db_select_result = subprocess.run(
        [
            "sqlite3",
            db_name,
            "select name from files where id=" + str(expected_file_db_id) + ";",
        ],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    try:
        assert db_select_result.stdout[:-1] == modify_file
    except AssertionError:
        process_handle.terminate()
        subprocess.run("kill -KILL " + str(process_handle.pid + 1), shell=True)
        os.remove(file_path + modify_file)
        raise
    # Teardown
    process_handle.terminate()
    subprocess.run("kill -KILL " + str(process_handle.pid + 1), shell=True)
    os.remove(file_path + modify_file)
    teardown


# Modify media file in monitored path
def test_modify_media_file():
    # Setup
    setup
    shutil.copy2(file_path + origin_file, file_path + destination_file)
    discoverer_handle = discoverer_run_once()
    discoverer_handle.start()
    time.sleep(3)
    expected_file_db_id = int(get_max_id_db())
    # Test
    os.rename(file_path + destination_file, file_path + modify_file)
    time.sleep(3)
    discoverer_handle = discoverer_run_once()
    discoverer_handle.start()
    time.sleep(3)
    db_select_result = subprocess.run(
        [
            "sqlite3",
            db_name,
            "select name from files where id=" + str(expected_file_db_id) + ";",
        ],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    assert db_select_result.stdout[:-1] == modify_file
    assert int(get_max_id_db()) == expected_file_db_id
    # Teardown
    os.remove(file_path + modify_file)
    teardown


# Database error table
def test_error_table():
    # Setup
    setup
    discoverer_handle = discoverer_run_once()
    discoverer_handle.start()
    time.sleep(3)
    # Test
    db_select_result = subprocess.run(
        [
            "sqlite3",
            db_name,
            "select errors.error_log from errors inner join files on files.id=errors.file_id where files.name = "
            + error_file
            + ";",
        ],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    # Main keywords that should appear in all reported errors
    assert error in db_select_result.stdout
    assert gst in db_select_result.stdout
    # Teardown
    teardown
