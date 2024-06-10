# fst-runtime

This project represents a Python package to query finite-state transducers that have been compiled to the AT&T format.

# Setup

```bash
python3 -m venv venv
./venv/bin/pip -U pip setuptools
./venv/bin/pip install poetry
ln -s ./venv/bin/poetry
```

## Running the Program

This program is still in early development and testing, and so "running the program" constitutes running the `fst-runtime` module as `'__main__'`.

To run this program with a test file, pass the file path to the `ATT_FILE_PATH` environment variable during program execution.

```bash
./poetry shell
ATT_FILE_PATH='./tests/data/fst1.att' LOG_LEVEL='DEBUG' python3 -m fst-runtime.fst 'input_string'
```
