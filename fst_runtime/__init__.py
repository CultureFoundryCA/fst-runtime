"""
fst-runtime

This package acts as a lightweight runtime for querying finite-state transducers (FSTs) stored in the AT&T ``.att`` format.

The development of this package was motivated by the need for a lightweight way to run FSTs compiled with foma or other toolkits in Python,
separate from the compilation technology. Previously, installing all of foma into a Docker container and compiling by source was necessary
to query the FST during deployment. This package provides a solution to that.

Note
----
Epsilon in this AT&T format is represented by the string '@0@'.

This package is used via the ``Fst`` object. This object requires a path to the AT&T-compiled FST, e.g., ``fst = Fst('/path/to/file.att')``.
You can get the multi-character symbols used in the FST via ``fst.multichar_symbols``.

The ``Fst`` object has a public method named ``down_generation``, which follows the FST convention of the "down" direction being the
direction of "generation" (i.e., creating forms from some tagged word form). For example, in English, for the lemma "do" with
possible affixes of ``prefixes = [['de', 'un']]`` and ``suffixes = [['+VERB'], ['+GER', '+INF', '+PAST']]``,
the call would be ``fst.down_generation([['un']], 'do', [['+VERB'], ['+GER', '+INF', '+PAST']])``.
This would return ``['do', 'doing', 'did', 'undo', 'undoing', 'undid']``.
"""

import logging

logger = logging.getLogger(__name__)
