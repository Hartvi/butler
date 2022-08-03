from __future__ import print_function, division

import os
from datetime import datetime
import json
from copy import deepcopy
import numpy as np
import re
from datetime import datetime as dt

import config

file_dirs = ("data", "figs", "imgs")
date_template = '%Y_%m_%d_%H_%M_%S'
max_date = '9999_12_31_23_59_59'
min_date = '0000_01_01_00_00_00'


def compare_interval(rm_str, start, end):
    """"""
    def f(str_date):
        x_strp_time = dt.strptime("_".join(str_date.replace(rm_str, "").split("_")[:6]), date_template)
        return start < x_strp_time < end

    return f


def update_json(p, update_dict):
    """Update the JSON dictionary on the path `p` with the dictionary `update_dict`.

    Parameters
    ----------
    p : str
        The path to the file to be updated.
    update_dict : dict
        The dictionary to be dumped into `p`.
    """
    with open(p, 'r+') as fp:
        existing_dict = json.load(fp)
        for c in update_dict:
            existing_dict[c] = update_dict[c]
        fp.seek(0)
        fp.truncate(0)
        json.dump(existing_dict, fp)


def replace_json(p, update_dict):
    """Dump the dictionary `update_dict` into the file `p` replacing it.

    Parameters
    ----------
    p : str
        The path to the file to be replaced.
    update_dict : dict
        The dictionary to be dumped into `p`.
    """
    with open(p, 'w') as fp:
        # existing_dict = json.load(fp)
        # for c in update_dict:
        #     existing_dict[c] = update_dict[c]
        fp.seek(0)
        fp.truncate(0)
        json.dump(update_dict, fp)


def get_regex(d, pattern, filter_out_nones=True):
    """Get a value from a dictionary `d` based on the regex key `pattern`. NOTE: Takes the shortest matching key.

    Parameters
    ----------
    d : dict
        The dict.
    pattern : str
        Any regex. E.g. `r".*property.*"` = any string containing `"property"`
    filter_out_nones : bool
        Whether to filter out all keys that correspond to `None` values

    """
    dk = d.keys()
    # a list of keys that match the regex
    key_arr = filter(lambda x: len(re.findall(pattern=pattern, string=x)) != 0, dk)
    if filter_out_nones:
        key_arr = filter(lambda x: d[x] is not None, key_arr)
    # sorted from shortest to longest
    ret_arr = sorted(key_arr, key=lambda y: len(y))
    if len(ret_arr) == 0:
        return None
    ret_key = ret_arr[0]
    return d[ret_key]


def get_recursive_regex(obj, pattern):
    # print("obj: ", obj)
    it = get_regex(obj, pattern)
    if it is not None:
        # print("returning:", it)
        return it
    for k, v in obj.items():
        # print("checking: k,v: ", k, v)
        if isinstance(v, dict):
            item = get_recursive_regex(v, pattern)
            if item is not None:
                # print("returning:", it)
                return item
    return None


def get_recursive(obj, key):
    if key in obj:
        return obj[key]
    for k, v in obj.items():
        if isinstance(v, dict):
            item = get_recursive(v, key)
            if item is not None:
                return item


# dd = {"lol": "1", "lo": 2, "nay": 3}
# p = r"lo.*"
# print(get_regex(dd, p))

def get_experiment_dirs(directory=config.experiment_directory, use_default_format=True, extra_rule=lambda x: "experiment" in x):
    """Returns all directories in `directory` that correspond to the format `experiment(_.*)x6` by default. E.g. experiment_2022_03_31_21_49_21.

    Parameters
    ----------
    directory : str
        The directory where the experiments are lcoated

    """
    ls_exp_dir = os.listdir(directory)
    experiment_dirs = ls_exp_dir
    if use_default_format:
        experiment_dirs = filter(lambda x: len(x.split("_")) == 7, ls_exp_dir)
    if extra_rule is None:
        ret_dirs = experiment_dirs
    else:
        ret_dirs = filter(extra_rule, experiment_dirs)
    abs_experiment_dirs = list(map(lambda x: os.path.join(directory, x), ret_dirs))
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
    """A numpy.array immune json.dump

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





