# fst-runtime

This project represents a Python package to query finite-state transducers that have been compiled to the AT&T format.


## Dev README

### Setup

This sets up a virtual environment with poetry installed to manage dependencies.

```bash
python3 -m venv venv
./venv/bin/pip -U pip setuptools
./venv/bin/pip install poetry
ln -s ./venv/bin/poetry
./poetry install
```

### Running the Project

The project is not setup to be run directly; to do this, add `if __name__ == '__main__'` checks wherever you might want
to run the project directly. Otherwise, run things through our tests.

`./poetry run pytest`
`./poetry run pylint`

## Acknowledgements

We would like to thank Miikka Silfverberg for providing the FSTs in our `tests/data` folder, and to the [OjibweMorph repo](https://github.com/ELF-Lab/OjibweMorph) from UBC's ELF-Lab for providing the 'waabam' FST to use in our testing.
