# fst-runtime

This project represents a Python package to query finite-state transducers that have been compiled to the AT&T format.

To run program, type in quotes in poetry shell 
example: ATT_FILE='./tests/examples/fst1.att' python fst-runtime/graph_ops.py

```bash
python3 -m venv venv
./venv/bin/pip -U pip setuptools
./venv/bin/pip install poetry
ln -s ./venv/bin/poetry
```

## Running the Program

This program is still in early development and testing, and so "running the program" constitutes running the `fst-runtime.graph_ops` module as `'__main__'`.

To run this program with a test file, pass the file path to the `ATT_FILE` environment variable during program execution.

```bash
./poetry shell
ATT_FILE='./tests/examples/fst1.att' python3 -m fst-runtime.graphops
```
