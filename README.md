# flume
Media scanner and indexer for your media files.

## Installation

## System dependencies
Besides the dependencies of the package itself, your system needs to have:
* gstreamer-1.0

## Usage
You need to provide a configuration on either `$HOME/.flume` or a system wide configuration at `/etc/flume`. The database parameters are modeled in the same way as `SQLAlchmey` URL parameters.

Sample configuration for sqlite3 database driver
```ini
[Database]
uri=sqlite:///flume.db

[Media]
dir=/home/user/Videos
```

## Development
Install poetry
```
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
```
Install dependencies
```
poetry install
```
Install pre-commit hooks
```
poetry run pre-commit install
```

## License
