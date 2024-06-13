# fst-runtime

This project represents a Python package to query finite-state transducers that have been compiled to the AT&T format.

## Setup

```bash
python3 -m venv venv
./venv/bin/pip -U pip setuptools
./venv/bin/pip install poetry
ln -s ./venv/bin/poetry
./poetry install
```

## Running the Tests

`./poetry run pytest`
