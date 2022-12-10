"""
This module contains compatibility functions. \n
It may also overwrite builtins to fix bugs from older versions.
(NOTE: all changes to builtins are ONLY bugfixes
 and do not change the behaviour in ANY way compared to up-to-date versions.) \”
This means that importing this module has side-effects
and thus the import should not be removed merely because the module is not used.
"""
"""
    Copyright (C) 2021  Robin Albers
"""
import builtins

import numpy as np
from packaging.version import parse as versionParser #TODO: Use AgeLib Version Parser to not rely in packaging


#region round-hack
if versionParser(np.__version__) < versionParser("1.19"): # numpy version less than 1.19
    builtins._round = builtins.round
    def __round(number, ndigits: float = None):
        """
        This function is exactly the same as the built-in round function. \n
        the only difference is, that this function casts the input to a float. \n
        This is done due to a numpy bug that caused `round(numpy.float64)` returned a `numpy.float64`
        instead of an integer (round is supposed to always return an integer when no precision is given). \n
        (Read more here: https://github.com/numpy/numpy/issues/11810 ). \n
        This function ensures correct behaviour across all numpy versions.
        """
        return builtins._round(float(number),ndigits)
    builtins.round = __round # This overload ensures that round behaves correctly.
    # since this overload only slightly increases the runtime and does not affect
    # the standard behaviour at all (except for fixing this weird bug) it should not lead to any confusion.
#endregion round-hack
