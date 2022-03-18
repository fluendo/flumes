<div align="center">
  <h1>Flumes
  <h4>Scan and index your media files</h4>
<div align="center">
  
  <a href="">[![PyPI version](https://badge.fury.io/py/flumes.svg)](https://badge.fury.io/py/flumes)</a>
  <a href=""><img alt="GitHub release (latest by date)" src="https://img.shields.io/github/v/release/fluendo/flumes"></a>
  <a href=""><img alt="Maintenance" src="https://img.shields.io/maintenance/yes/2022"></a>
  <a href=""><img alt="GitHub pull requests" src="https://img.shields.io/github/issues-pr/fluendo/flumes"></a>
  <a href="">[![ci](https://github.com/fluendo/flumes/actions/workflows/ci.yml/badge.svg)](https://github.com/fluendo/flumes/actions/workflows/ci.yml) </a>
  <a href="">[![cd](https://github.com/fluendo/flumes/actions/workflows/cd.yml/badge.svg)](https://github.com/fluendo/flumes/actions/workflows/cd.yml)</a>
  <a href="">[![License](https://img.shields.io/github/license/fluendo/flumes.svg)](https://github.com/fluendo/flumes)</a>
  <a href=""><img alt="Website" src="https://img.shields.io/website?label=fluendo.com&up_color=blue&up_message=flumes&url=https%3A%2F%2Ffluendo.com"></a>

  
</div>
</div><br>
  
## Table of Contents
- [About The Project](#about_the_project)
- [Getting Started](#getting_started)
  - [System requirements](#system_requirements)
  - [Installation](#installation)  
    - [Poetry](#poetry)
    - [Docker](#docker)
  - [Troubleshooting](#troubleshooting)
- [Usage](#usage)
  - [Querying the database](#querying_the_database)
  - [Trigger rescan](#trigger_rescan)
- [Development](#development)
  - [Required dependencies](#required_dependencies)
  - [Git hook](#git_hook)
  - [New releases](#new_releases)
  - [Tagging](#tagging)
  - [Database](#database)
  - [Testing](#testing)
- [License](#license)

## About The Project <a name = "about_the_project"></a>
Flumes is a tool that allows you to select a folder and detect existing media files automatically. These media files are scanned and all relevant information is stored in a database. In addition, you can trigger a scan manually anytime to update your database.

**Features**
* Scan media files in a selected directory
* Automatically rescan selected media directory when changes are detected
* Stores the `GstDiscoveryStream` information and the `GstCaps` structure fields in a database
* Trigger directory rescan manually

## Getting Started <a name = "getting_started"></a>
**System requirements** <a name = "system_requirements"></a>

* Operating system: Linux 64-bit
  
* [gstreamer-1.0](https://gstreamer.freedesktop.org/download/)
  ```
  gst-launch-1.0 --gst-version
  ```
  
* [Gio >=2.62](https://docs.gtk.org/gio/)
  ```
  gio version
  ```
  
* [Python >=3.9](https://www.python.org/downloads/)
* [Docker](https://docs.docker.com/engine/install/ubuntu/) *Only required for installation via Docker. [See here](#docker)*
* [Docker Compose](https://docs.docker.com/compose/install/#install-compose) *Only required for installation via Docker. [See here](#docker)*

**Installation** <a name = "installation"></a>

For a successful and complete installation, you can choose between the Poetry packaging and dependency management tool or just use Docker.

1. If you select via [*Poetry*](https://python-poetry.org/docs/): <a name = "poetry"></a>

Make sure you are on the root path of the project before running these commands.

* Install poetry
```
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
```
* Install dependencies
```
poetry install
```
* Link the database to the folder where you want to monitor your media files:
```
poetry run flumes-discovery -i sqlite:///flumes.db -d <media content directory>  
```
2. In case you prefer an alternative to *poetry* for installation, you can use it via [*Docker*](https://www.docker.com/): <a name = "docker"></a>
```
docker-compose -f docker-compose-dev.yml up --build
```

**Troubleshooting** <a name = "troubleshooting"></a>

- gi module:

If `error ModuleNotFoundError: No module named 'gi'"` , check your installation:
  
```  
sudo apt install libgirepository1.0-dev gcc libcairo2-dev pkg-config python3-dev gir1.2-gtk-3.0
pip3 install pycairo
pip3 install PyGObject
```

- Sometimes there could be differences between the version of python in your virtual environment and the version to install during setup. In this case, check that both versions match.
```
sudo apt-get install python<version>-dev
```

## Usage <a name = "usage"></a>
**Querying the database** <a name = "querying_the_database"></a>

SQLite is the database engine used to store all the information collected in the scanning process through discovery. You can see how this database is created in the `schema.py` file and implemented through its migrations.
sqlite3 will allow you to manually enter and execute SQL queries against your SQLite database as follows:
```
sqlite3 flumes-dev.db 
```
Now you can make any query to your media files indexed in the database.

**Trigger rescan** <a name = "trigger_rescan"></a>

You can trigger discovery to rescan all files at run time.
Either locally or using [*poetry*](#poetry) you can look up the PID and send the corresponding signal:
* Select the PID where flumes-discovery is running
```
ps aux | grep flumes-discovery
```
* Send the signal to rescan
```
kill -USR1 <PID>
```


Also this feature is available to use through [*docker*](#docker):
* Find the running container's ID:
```
docker ps
```
* Check the Process ID (PID):
```
docker exec -it <container ID> ps -aux
```
* Now, you can send various signals to trigger the rescan:
```
docker exec -t -i <container ID> /bin/sh -c 'kill -USR1 <PID>'
```

## Development <a name = "development"></a>

**Required dependencies** <a name = "required_dependencies"></a>

The installation via [*poetry*](#poetry) and [*docker*](#docker) will install all the required dependencies by default but in case you do not use any of these options the installation will not be completed. To successfully guarantee your development process, check that you have the following dependencies installed:
* python-dateutil = ^2.8.2
* SQLAlchemy = ^1.4.26
* alembic = ^1.7.5
* packaging = ^21.3
* pytest = ^5.2
* pre-commit = ^2.15.0
* black = ^21.9b0
* isort = ^5.9.3
* tox = ^3.24.4
* yamllint = ^1.26.3

**Git hook** <a name = "git_hook"></a>

You can detect any issue before commit using pre-commit hooks.
* Install pre-commit hooks
```
poetry run pre-commit install
```

**New releases** <a name = "new_releases"></a>

To generate a new release you must update the version number. The following files will need to be updated: 
* init file
* tests/test_flumes.py
* pyproject.toml

Once it is merged, tagging must be done in order to distribute the new version correctly.

**Tagging** <a name = "tagging"></a>

```
git tag -a <version> -m "Release <version>"
```
```
git push origin --tags
```

**Database** <a name = "database"></a>

You must use alembic for database migration. First, make the necessary changes to the `schema.py` file and then proceed with the steps to successfully perform the migration.
```
alembic revision --autogenerate
```
```
alembic upgrade head
```
```
alembic stamp head
```

**Testing** <a name = "testing"></a>

All tests are located in the tests folder. The framework used is [*pytest*](https://docs.pytest.org/). 
You can run the tests locally using the following command under the same path for example:
```
poetry run pytest
```

## License <a name = "license"></a>
See `LICENSE.LGPL` for more information.
