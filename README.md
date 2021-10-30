# Flume: Media indexing
## Usage
Sample configuration
```
[Database]
uri=sqlite:///flume.db
user=user
password=password
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
Pre-commit hooks
```
poetry run pre-commit install
```
