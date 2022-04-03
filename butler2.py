from __future__ import print_function, division

import sys
import os
from io import BytesIO as StringIO
from datetime import datetime
import json
import numpy as np
import re
from copy import deepcopy

real_std_out = None


def dump_numpy_proof(something, fp):
    something = numpy_to_native(something)
    json.dump(something, fp)


def numpy_to_native(something, inplace=False):
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
        for i,k in enumerate(new_something):
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


class CustomStringIO(StringIO):
    def write(self, data):
        real_std_out.write(data)
        # real_std_out.write("\n"+str(super(CustomStringIO, self).__dict__))
        super(CustomStringIO, self).write(data)  # this is writing into BytesIO, so it might need `data.encode()`


def get_time_string():
    time_string = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    return time_string


def this_dir():
    real_path = os.path.realpath(__file__)
    dir_path = os.path.dirname(real_path)
    return dir_path


def cache_print(f, *args, **kwargs):
    """
    Save the return value of f & prints from this function in a tuple:: (return values, prints)
    :param f: function
    :param args: args
    :param kwargs: kwargs
    :return: (f(args, kwargs), stdout of the function as a string)
    """
    global real_std_out
    real_std_out = sys.stdout
    sys.stdout = mystdout = CustomStringIO()
    ret = f(*args, **kwargs)

    sys.stdout = real_std_out
    return ret, mystdout.getvalue()


DirectoryStructure = {
    "name":
        "exp_{}",
    "structure":
        {
            "log": "log.txt",
            # "setup": "/home/robot3/vision_ws/src/ipalm_control/butler/setup.json",
            "setup_json": "setup.json",
            "timestamp": "timestamp_{}"
        }
}

PropertyStructure = {
    "name": "{}",
    "structure": {
        "log": "log.txt",
        "imgs": "imgs",
        "figs": "figs",
        "data": {
            "name":
                "data",
            "structure":
                {
                    "meas":
                        {
                            "name": "meas.json",
                            "properties":
                                [
                                    "avg",
                                    "std"
                                ]
                        },
                },
        },
    }
}


class Butler:
    session_exists = False
    session_paths = None
    property_setup = dict()

    @staticmethod
    def get_free_num(str_in):
        split_str = str_in.split("_")
        if os.path.isfile(str_in):
            return 0
        if len(split_str) != 2:
            return 0
        return int(split_str[1]) + 1

    @staticmethod
    def create_directory_tree_for_session(parent_dir, setup):
        existing_directories = os.listdir(os.path.dirname(__file__))
        # get the lowest unused number that isn't lower than any other number in this dir
        lowest_num = max(map(Butler.get_free_num, existing_directories))

        new_exp_path = os.path.join(parent_dir, DirectoryStructure["name"].format(lowest_num))
        new_log_path = os.path.join(new_exp_path, DirectoryStructure["structure"]["log"])
        new_setup_json_path = os.path.join(new_exp_path, "setup.json")
        new_time_stamp_path = os.path.join(new_exp_path,
                                           DirectoryStructure["structure"]["timestamp"].format(get_time_string()))

        # create dirs & files
        os.mkdir(new_exp_path)
        with open(new_log_path, "w") as fp:
            pass
        with open(new_setup_json_path, "w+") as fp:
            dump_numpy_proof(setup, fp)
        with open(new_time_stamp_path, "w") as fp:
            pass
        ret = dict()
        ret["exp"] = new_exp_path
        ret["log"] = new_log_path
        ret["setup"] = new_setup_json_path
        return ret

    @staticmethod
    def create_property_entry(parent_dir, meas_dict):
        j = os.path.join
        prop_struct = PropertyStructure["structure"]

        ls_exp = os.listdir(parent_dir)
        next_index = 0
        for n in ls_exp:
            if meas_dict["meas_prop"] in n:  # "mass" in "mass_0"
                next_index = int(n.split("_")[-1]) + 1

        new_prop_dir = j(parent_dir, meas_dict["meas_prop"] + "_" + str(next_index))
        imgs_dir = j(new_prop_dir, prop_struct["imgs"])
        figs_dir = j(new_prop_dir, prop_struct["figs"])
        data_dir = j(new_prop_dir, prop_struct["data"]["name"])
        log_file = j(new_prop_dir, prop_struct["log"])
        meas_file = j(data_dir, prop_struct["data"]["structure"]["meas"]["name"])
        new_dirs = [new_prop_dir, imgs_dir, figs_dir, data_dir]
        new_files = [log_file, meas_file]
        for d in new_dirs:
            new_dir_name = d
            new_index = 0
            while os.path.isdir(new_dir_name):  # idk why but just in case the directory exists here
                new_split = new_dir_name.split("_")
                try:
                    new_index = int(new_split[-1]) + 1
                except:
                    new_index = 0
                new_name = ""
                for _ in range(len(new_split) - 1):
                    new_name += new_split[_] + "_"
                new_dir_name = new_name + str(new_index)
            os.mkdir(new_dir_name)
        for f in new_files:
            with open(f, "w") as f:
                pass
        with open(meas_file, "w") as f:
            dump_numpy_proof(meas_dict, f)

        ret = dict()
        ret["property"] = new_prop_dir
        ret["imgs"] = imgs_dir
        ret["figs"] = figs_dir
        ret["data"] = data_dir
        ret["log"] = log_file
        ret["meas"] = meas_file
        return ret

    @staticmethod
    def _update_internal_setup(setup_dict):  # atm only the last used setup for the given quantity
        setups_path = os.path.join(this_dir(), "setups")
        if not os.path.isdir(setups_path):
            Butler.setups_folder = setups_path
            os.mkdir(setups_path)
        setups_path = os.path.join(setups_path, "setups.json")
        if not os.path.isfile(setups_path):
            with open(setups_path, "w") as fp:
                fp.write("{}")
        with open(setups_path, "r") as fp:
            current_exp_setup = json.load(fp)
        with open(setups_path, "w") as fp:
            current_exp_setup[get_time_string()] = setup_dict
            dump_numpy_proof(current_exp_setup, fp)

    @staticmethod
    def butler(keywords=(),
               keep_keywords=True,
               setup_file="setup.json",
               delimiter="\n",
               add_new_line=True,
               catch_return=True,
               session_parent_dir=os.path.dirname(__file__),
               meas_object_name="",
               data_variables=(),
               ignore_colours=True,
               create_new_exp_on_run=False):
        assert type(meas_object_name) == str, "measured object variable name must be string! & Only one per function"
        assert type(keywords) == str or type(keywords) == list or type(keywords) == tuple,\
            "keywords must be of type str or list[str]"

        try:
            with open(setup_file, "r") as fp:
                Butler.setup = json.load(fp)
        except IOError as e:
            raise IOError(
                "\n1. setup.json is not located in session_parent_dir="+session_parent_dir+
                " or \n2. the `session_parent_dir` containing the `setup.json` is not specified.\n"
                "Please add a setup file in the format\n"
                "{\"arm\": \"arm_name\", "
                "\"gripper\": \"gripper_name\", "
                "\"algorithm\": \"http://link_to_repository/\", "
                "\"camera\": \"camera_model_name\", "
                "\"microphone\":\"microphone_model_name\", "
                "\"other:\" \"other_modalities\"}\n"
                "Leave fields empty if you are not using them.")
        if Butler.session_paths is None and not create_new_exp_on_run:
            Butler.session_paths = Butler.create_directory_tree_for_session(parent_dir=session_parent_dir, setup=Butler.setup)

        def decorated(f):
            def wrapper(*args, **kwargs):
                if create_new_exp_on_run:
                    Butler.session_paths = Butler.create_directory_tree_for_session(parent_dir=session_parent_dir,
                                                                                    setup=Butler.setup)
                res, captured_std_out = cache_print(f, *args, **kwargs)
                processed_std_out = captured_std_out
                if ignore_colours:
                    processed_std_out = re.sub(r"\033\[\d+(;\d+)?m", "", captured_std_out)

                """general log"""
                with open(Butler.session_paths["log"], "a") as fp:
                    fp.write(processed_std_out)

                """single property logs, etc."""
                """meas_prop, meas_type, params, values, meas_ID"""
                if catch_return:
                    if type(res) == tuple:
                        new_measurement = res[0].__dict__
                    else:
                        new_measurement = res.__dict__
                else:
                    new_measurement = eval("butler." + meas_object_name).__dict__

                property_paths = Butler.create_property_entry(Butler.session_paths["exp"], new_measurement)
                # the prints containing `keywords` go into property_paths["log"]
                property_log = property_paths["log"]

                Butler._update_internal_setup(Butler.setup)

                variables_in_tuple = type(data_variables) == tuple and not type(data_variables) == dict
                for v in data_variables:
                    new_v_name = v.replace("self.", "")
                    if "self." in v:
                        data_variable = args[0].__dict__[new_v_name]
                    else:
                        data_variable = eval(new_v_name)
                    if variables_in_tuple:
                        with open(os.path.join(property_paths["data"], new_v_name+".json"), "w") as fp:
                            dump_numpy_proof(data_variable, fp)
                    else:
                        with open(os.path.join(property_paths["data"], data_variables[v]+".json"), "w") as fp:
                            dump_numpy_proof(data_variable, fp)
                tmp_keywords = keywords
                if type(keywords) == str:
                    tmp_keywords = [keywords, ]
                print_split = processed_std_out.split(delimiter)
                butlered_lines = ""
                for kwd in tmp_keywords:
                    for prnt in print_split:
                        if kwd in prnt:
                            if keep_keywords:
                                butlered_lines += prnt + ("\n" if add_new_line else "")
                            else:
                                butlered_lines += prnt.replace(kwd, "") + ("\n" if add_new_line else "")

                # butlered_lines goes to exp_{}/meas_prop/log.txt
                with open(property_log, "w") as fp:
                    fp.write(butlered_lines)
                return res
            return wrapper
        return decorated


butler = Butler.butler  # to make `from butler2 import butler` possible


if __name__ == "__main__":
    class MeasObject:
        """
        "density", "continuous", {"mean": 100, "sigma": 10}, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], meas_ID=1
        """

        def __init__(self, meas_prop, meas_type, params, values, meas_ID):
            self.meas_prop = meas_prop  # eg mass, elasticity, vision, sound
            self.meas_type = meas_type  # continuous, discrete
            self.params = params  #
            self.values = values
            self.meas_ID = meas_ID

        def __repr__(self):
            rep = ""
            rep += "------ID:{}------\n".format(self.meas_ID)
            rep += "Property: {} of type: {}\n".format(self.meas_prop, self.meas_type)
            rep += "Params: {}\n".format(self.params)
            rep += "Some Values: {}...{}\n".format(self.values[0:5], self.values[-5:])
            return rep


    class TestClass:
        def __init__(self):
            self.test_value1 = [1, 2, 3, 4, 5, 6, 7, 8, 9]
            self.test_value2 = [9, 8, 7, 6, 5, 6, 7, 8, 9]

        @butler("[INFO]", delimiter="\n", data_variables=("self.test_value1",), create_new_exp_on_run=True)
        def multiply(self, a, b):
            _meas = MeasObject("elasticity", "continuous", {"mean": 500000, "std": 100000},
                               [1, 5, 8, 5, 2, 7, 5, 1, 3, 8, 7, 1, 5, 8, 85, 1, 5, 8, 8, 4, 12, 65], 6)
            print("this should only be in the top log")
            print("[INFO] no thanks")

            stringlol = "\033[1;31m Sample Text \033[0m"
            print(stringlol)
            print("result: ", a * b)
            # print(dir())
            return _meas, a * b

        @butler("[INFO]", delimiter="\n", keep_keywords=False, data_variables=("self.test_value2",),
                create_new_exp_on_run=True)
        def divide(self, a, b):
            _meas = MeasObject("stiffness", "continuous", {"mean": 500000, "std": 100000},
                               [1, 5, 8, 5, 2, 7, 5, 1, 3, 8, 7, 1, 5, 8, 85, 1, 5, 8, 8, 4, 12, 65], 6)
            print("this should only be in the top log")
            print("[INFO] divide baby [INFO]")
            stringlol = "\033[1;31m Sample Text \033[0m"

            print(stringlol)
            print("result: ", a / b)
            # print(dir())
            return _meas, a / b


    all_vars = dir()
    bc = TestClass()
    c = bc.multiply(39, 20)
    d = bc.divide(40, 20)
    print(eval("__file__"))



