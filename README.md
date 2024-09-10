# fst-runtime

The `fst_runtime` python package is written as a light-weight front-end for finite-state transducers compiled to AT&T's `.att` format via programs like foma, hfst, etc. This runtime reads the FST into memory from the `.att` file, and publishes two main query functions, `down_generation` and `up_analysis`, that walk the FST either down (`wal+VERB+GER -> walking`) or up (`walking -> wal+VERB+GER`), respectively.

There are also methods for bulk querying, `down_generations` and `up_analyses`.

Documentation for this project can be found at [https://culturefoundryca.github.io/fst-runtime/](https://culturefoundryca.github.io/fst-runtime/).

## Installation Instructions

This package is published on PyPI and can be installed via `pip install fst_runtime` or `poetry add fst_runtime`, etc.

## Weighted FSTs

This runtime supports weighted FSTs, where the weights are defined under a semiring. Common semirings are provided via `fst_runtime.semiring`.

## Example Usage

```python
from fst_runtime.fst import Fst

fst = Fst('/home/username/fsts/walk.att')

generations = fst.down_generation('wal', suffixes=[['+VERB'], ['+GER', '+INF']])

for generation in generations:
    print(generation)
```

This example, based off of `tests/data/fst4.att`, would then return the results of `wal+VERB+GER` and `wal+VERB+INF` which would be `['walking', 'walk']`. If you simply called `fst.down_generation('wal')`, it would generate all possible wordforms of it in the FST.

Similarly with up:

```python
analyses = fst.up_analysis('walking')

for analysis in analyses:
    print(analysis)
```

In this case, we only get one result back, `wal+VERB+GER`.

## Acknowledgements

We would like to thank Dr. Miikka Silfverberg for his help in deciding what this application should look like, and for providing test FSTs for us to use to test the application.

We would also like to thank UBC's ELF-Lab for the use of the `waabam` walk through their fully-fledged Ojibwe FST. You can find their repo here: [https://github.com/ELF-Lab/OjibweMorph](https://github.com/ELF-Lab/OjibweMorph).

Also thank you to Sandra Radic for some early application code.

## Development

For working on this project, please consult [the wiki](https://github.com/CultureFoundryCA/fst-runtime/wiki/Project-Architecture) for the project's architecture and dev setup. PRs welcome.
