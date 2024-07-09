'''
fst-runtime

This package acts as a lightweight runtime for querying finite-state transducers (FSTs) stored in the AT&T `.att` format.
The development of this package was motivated by the fact that FSTs compiled with foma or other toolkits don't have a
lightweight way of being ran in Python that is separate from the compilation technology. In our case, we had to install all
of foma into a docker container, compiling by source, just to query the FST during deployment. This package is the solution
to that.

Note that epsilon in this AT&T format is represented by the string '@0@'.

This package is used via the `Fst` object. This object requires a path to the AT&T-compiled FST, i.e. `fst = Fst('/path/to/file.att')`.
You can get the multi-character symbols used in the FST via `fst.multichar_symbols`.

The `Fst` object has a public method named `down_generation`. This is in keeping with FST convention of the "down" direction being
the direction of "generation"; that is, creating forms from some sort of tagged word form. For example in English, for the lemma "do"
with possible affixes of `prefixes = [['de', 'un']]` and `suffixes = [['+VERB'], ['+GER', '+INF', '+PAST']]`, we would have our call
be made as `fst.down_generation(prefixes, lemma, suffixes) = fst.down_generation([['un']], 'do', [['+VERB'], ['+GER', '+INF', '+PAST']]).
This would then return ['do', 'doing', 'did', 'undo', 'undoing', 'undid'].

Support for `up_analysis` is pending.

'''

import logging

logger = logging.getLogger(__name__)
