# flumes
Media scanner and indexer for your media files.

## Features
* Re-scan after media directory changes
* Stores the `GstDiscoveryStream` information and the `GstCaps` strcuture fields

## Installation

## System dependencies
Besides the dependencies of the package itself, your system needs to have:
* gstreamer-1.0
* Gio >=2.62

## Usage
You need to provide a configuration on either `$HOME/.flumes` or a system wide configuration at `/etc/flumes`. The database parameters are modeled in the same way as `SQLAlchemy` URL parameters.

Sample configuration for sqlite3 database driver
```ini
[Database]
uri=sqlite:///flumes.db
```

Link the database to the folder:
```
poetry run flumes-discovery -i sqlite:///flumes.db -d <media content directory>  
```

Alternatively, use Dockerfile for development:
```
docker-compose -f docker-compose-dev.yml up
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

## New releases
Upgrade release version number here:
* __init__.py file
* tests/test_flumes.py
* pyproject.toml

Tagging:
```
git tag -a "<version>" -m "Release <version>"
```
```
git push origin --tags
```

## Database
You must use alembic for database migration:
```
alembic revision --autogenerate
```
```
alembic upgrade head
```
```
alembic stamp head
```
