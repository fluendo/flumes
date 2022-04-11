import os
import shutil
import signal
import subprocess
import time

from .conftest import *


# Content on usr1 signal function test
def test_on_usr1_signal(discoverer):
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


# Copy media file to monitored path
def test_discover_newly_copied_file():
    # Setup
    discoverer_setup = discoverer_run_once()
    discoverer_setup.start()
    expected_file_db_id = int(max_db_id()) + 1
    # Test
    shutil.copy2(file_path + origin_file, file_path + destination_file)
    discoverer_test = discoverer_run_once()
    discoverer_test.start()
    db_select_result = subprocess.run(
        [
            "sqlite3",
            db_name,
            "select name from files where id={};".format(expected_file_db_id),
        ],
        capture_output=True,
        text=True,
        cwd="tests",
    )
    db_select_result.check_returncode()
    assert db_select_result.stdout[:-1] == os.path.basename(destination_file)
    assert db_select_result.stderr == ""
    # Teardown
    os.remove(file_path + destination_file)
    db_delete_result = subprocess.run(
        [
            "sqlite3",
            db_name,
            "delete from files where id={};".format(expected_file_db_id),
        ],
        capture_output=True,
        text=True,
        cwd="tests",
    )
    db_delete_result.check_returncode()


# Delete media file from monitored path
def test_discover_removed_file():
    # Setup
    shutil.copy2(file_path + origin_file, file_path + destination_file)
    discoverer_test = discoverer_run_once()
    discoverer_test.start()
    assert int(max_db_id()) == 2
    # Test
    os.remove(file_path + destination_file)
    discoverer_test = discoverer_run_once()
    discoverer_test.start()
    assert int(max_db_id()) == 1


# Trigger manual rescan
def test_manual_rescan():
    # Setup
    shutil.copy2(file_path + origin_file, file_path + destination_file)
    process_handle = subprocess.Popen(flumes_discoverer, shell=True)
    time.sleep(6)
    os.rename(file_path + destination_file, file_path + modify_file)
    # Test
    subprocess.run("kill -USR1 " + str(process_handle.pid), shell=True)
    time.sleep(6)
    db_select_result = subprocess.run(
        ["sqlite3", db_name, "select name from files where id=2;"],
        capture_output=True,
        text=True,
        cwd="tests",
    )
    time.sleep(1)
    assert db_select_result.stdout[:-1] == modify_file
    # Teardown
    process_handle.terminate()
    subprocess.run("kill -KILL " + str(process_handle.pid + 1), shell=True)
    time.sleep(3)
    os.remove(db_rel_path)
    os.remove(file_path + modify_file)
