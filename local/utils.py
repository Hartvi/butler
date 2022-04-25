from __future__ import print_function, division

import os
from datetime import datetime
import json
from copy import deepcopy
import numpy as np

import conf

file_dirs = ("data", "figs", "imgs")


def get_all_experiment_dirs(directory=conf.experiment_directory):
    ls_exp_dir = os.listdir(directory)
    experiment_dirs = filter(lambda x: len(x.split("_")) == 7, ls_exp_dir)
    abs_experiment_dirs = list(map(lambda x: os.path.join(directory, x), experiment_dirs))
    return abs_experiment_dirs


def get_time_string():
    """Returns the timedate formatted in %Y_%m_%d_%H_%M_%S

    Return
    ------
    str
        Formatted timedate in descending order of significance
    """
    time_string = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    return time_string


def dump_numpy_proof(something, fp):
    """A np.ndarray immune json.dump(sth, fp)

    Parameters
    ----------
    something : list or tuple of np.ndarray or dict or set
        Object to convert to json.

    """
    something = numpy_to_native(something)
    json.dump(something, fp)


def numpy_to_native(something, inplace=False):
    """Recursively converts np.ndarrays to lists inside all combinations of nested lists, tuples, dicts, sets

    Parameters
    ----------
    something : list or tuple or dict or set or np.ndarray
        It has too many np.ndarrays.
    inplace : bool
        Whether to overwrite the something in-place

    Returns
    -------
    list or tuple or dict or set
        A denumpyified something
    """
    if inplace:
        new_something = something
    else:
        new_something = deepcopy(something)
    if type(new_something) == np.ndarray:
        new_something = new_something.tolist()
    if type(new_something) == dict:
        for k in new_something:
            if type(new_something[k]) == np.ndarray:
                new_something[k] = new_something[k].tolist()
            if type(new_something[k]) == dict:
                new_something[k] = numpy_to_native(new_something[k])
            elif type(new_something[k]) == list:
                new_something[k] = numpy_to_native(new_something[k])
    elif type(new_something) == list:
        for i, k in enumerate(new_something):
            if type(k) == np.ndarray:
                new_something[i] = k.tolist()
            if type(k) == dict:
                new_something[i] = numpy_to_native(k)
            elif type(k) == list:
                new_something[i] = numpy_to_native(k)
    elif type(new_something) == set:
        for k in new_something:
            if type(k) == np.ndarray:
                new_something.remove(k)
                new_k = k.tolist()
                new_something.add(new_k)
            if type(k) == dict:
                new_something.remove(k)
                new_k = numpy_to_native(k)
                new_something.add(new_k)
            elif type(k) == list:
                new_something.remove(k)
                new_k = numpy_to_native(k)
                new_something.add(new_k)
    return new_something





