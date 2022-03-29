import sys
import os
from io import BytesIO as StringIO
from datetime import datetime
import json
import numpy as np


def unnumpyify(something):
    if type(something) == np.ndarray:
        something = something.tolist()
    if type(something) == dict:
        for k in something:
            if type(something[k]) == np.ndarray:
                something[k] = something[k].tolist()
            if type(something[k]) == dict:
                something[k] = unnumpyify(something[k])
            elif type(something[k]) == list:
                something[k] = unnumpyify(something[k])
    elif type(something) == list:
        for i,k in enumerate(something):
            if type(k) == np.ndarray:
                something[i] = k.tolist()
            if type(k) == dict:
                something[i]  = unnumpyify(k)
            elif type(k) == list:
                something[i] = unnumpyify(k)
    return something


# def get_next_number(in_str):
#     for i in range(len(in_str)):
#

# l = [2, 5, 1, 3, 8, 5, 4]
# b = ["el0", "el1", "el2", "el3", "el4", "el5", "el6"]
# b = np.array(b)
# print(b[np.argsort(l[::-1])])
#
# stringlol = "\033[1;31m Sample Text \033[0m"
import re
# line = re.sub(r"\033\[\d+m", "", stringlol)
# line = re.match(pattern=r"\033\[\d+;\d+m", string=stringlol)#(r"\033\[\d*;?\d+m", "", stringlol)
# print(line)
# line = re.match(pattern=r"\033\[\d+m", string=stringlol)#(r"\033\[\d*;?\d+m", "", stringlol)




def get_time_string():
    time_string = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    return time_string


def this_dir():
    real_path = os.path.realpath(__file__)
    dir_path = os.path.dirname(real_path)
    return dir_path


def print_callable(f):
    def decorated(*args, **kwargs):
        res = f(*args, **kwargs)
        print(res)
        return res
    return decorated


def cache_print(f, *args, **kwargs):
    """
    Save the return value of f & prints from this function in a tuple:: (return values, prints)
    :param f: function
    :param args: args
    :param kwargs: kwargs
    :return: (f(args, kwargs), stdout of the function as a string)
    """
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()
    ret = f(*args, **kwargs)

    sys.stdout = old_stdout
    return ret, mystdout.getvalue()


DirectoryStructure = {
    "name":
        "exp_{}",
    "structure":
        {
            "log": "log.txt",
            "setup": "/home/robot3/vision_ws/src/ipalm_control/butler/setup.json",
            "timestamp": "time_stamp{}"
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


def get_free_num(str_in):
    split_str = str_in.split("_")
    if os.path.isfile(str_in):
        return 0
    if len(split_str) != 2:
        return 0
    return int(split_str[1])+1


def create_directory_tree_for_session(parent_dir, setup):
    existing_directories = os.listdir(os.path.dirname(__file__))
    # get the lowest unused number that isn't lower than any other number in this dir
    lowest_num = max(map(get_free_num, existing_directories))

    new_exp_path = os.path.join(parent_dir, DirectoryStructure["name"].format(lowest_num))
    new_log_path = os.path.join(new_exp_path, DirectoryStructure["structure"]["log"])
    new_setup_json_path = os.path.join(new_exp_path, "setup.json")
    new_time_stamp_path = os.path.join(new_exp_path, "timestamp_"+get_time_string())

    # create dirs & files
    os.mkdir(new_exp_path)
    with open(new_log_path, "w") as fp:
        pass
    with open(new_setup_json_path, "w+") as fp:
        json.dump(setup, fp)
        # print("written {} into", new_setup_json_path)
        pass
    with open(new_time_stamp_path, "w") as fp:
        pass
    ret = dict()
    ret["exp"] = new_exp_path
    ret["log"] = new_log_path
    ret["setup"] = new_setup_json_path
    return ret


def create_property_entry(parent_dir, meas_dict):
    j = os.path.join
    prop_struct = PropertyStructure["structure"]

    ls_exp = os.listdir(parent_dir)
    next_index = 0
    # print(meas_dict["meas_prop"])
    for n in ls_exp:
        # print(n, meas_dict["meas_prop"] in n)
        if meas_dict["meas_prop"] in n:  # "mass" in "mass_0"
            next_index = int(n.split("_")[-1]) + 1

    new_prop_dir = j(parent_dir, meas_dict["meas_prop"]+"_"+str(next_index))
    imgs_dir = j(new_prop_dir, prop_struct["imgs"])
    figs_dir = j(new_prop_dir, prop_struct["figs"])
    data_dir = j(new_prop_dir, prop_struct["data"]["name"])
    log_file = j(new_prop_dir, prop_struct["log"])
    meas_file = j(data_dir, prop_struct["data"]["structure"]["meas"]["name"])
    # setup_file = j(new_prop_dir, prop_struct["setup"])
    new_dirs = [new_prop_dir, imgs_dir, figs_dir, data_dir]
    new_files = [log_file, meas_file]
    for d in new_dirs:
        new_dir_name = d
        os.mkdir(new_dir_name)
    for f in new_files:
        with open(f, "w") as f:
            pass
    with open(meas_file, "w") as f:
        
        meas_dict = unnumpyify(meas_dict)
        json.dump(meas_dict, f)
    ret = dict()
    ret["property"] = new_prop_dir
    ret["imgs"] = imgs_dir
    ret["figs"] = figs_dir
    ret["data"] = data_dir
    ret["log"] = log_file
    ret["meas"] = meas_file
    return ret


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


def butler(keywords, delimiter="\n", add_new_line=True,
           catch_return=True, keep_prints=True,
           session_parent_dir=os.path.dirname(__file__),
           meas_object_name="", data_variables=(),
           ignore_colours=True):
    assert type(meas_object_name) == str, "measured object variable name must be string! & Only one per function"
    assert type(keywords) == str or type(keywords) == list, "keywords must be of type str or list[str]"

    # if "setup.json" in os.listdir(session_parent_dir):
    with open(DirectoryStructure["structure"]["setup"], "r") as fp:
        butler.setup = json.load(fp)
    # else:
    #     raise IOError(
    #         "setup.json is not located in "+session_parent_dir+
    #         ". Please add a setup file in the format\n"
    #         "{\"arm\": \"arm_name\", "
    #         "\"gripper\": \"gripper_name\", "
    #         "\"algorithm\": \"link_to_repository\", "
    #         "\"camera\": \"camera_model_name\", "
    #         "\"microphone\":\"microphone_model_name\"}\n"
    #         "Leave fields empty if you are not using them.")
    butler.session_paths = create_directory_tree_for_session(parent_dir=session_parent_dir, setup=butler.setup)

    def decorated(f):
        def wrapper(*args, **kwargs):

            # variables exist after this function:
            res, mystdout = cache_print(f, *args, **kwargs)
            mynewstdout = mystdout
            if ignore_colours:
                mynewstdout = re.sub(r"\033\[\d+(;\d+)?m", "", mystdout)

            """general log"""
            with open(butler.session_paths["log"], "a") as fp:
                fp.write(mynewstdout)

            """single property logs, etc."""
            """meas_prop, meas_type, params, values, meas_ID"""
            if catch_return:
                if type(res) == tuple:
                    new_measurement = res[0].__dict__
                else:
                    new_measurement = res.__dict__
            else:
                new_measurement = eval("butler." + meas_object_name).__dict__

            property_paths = create_property_entry(butler.session_paths["exp"], new_measurement)
            # the prints containing `keywords` should go into property_paths["log"]
            property_log = property_paths["log"]

            _update_internal_setup(butler.setup)

            variables_in_tuple = type(data_variables) == tuple and not type(data_variables) == dict
            for v in data_variables:
                new_v_name = v.replace("self.", "")
                if "self." in v:
                    data_variable = args[0].__dict__[new_v_name]
                else:
                    data_variable = eval(new_v_name)
                if variables_in_tuple:
                    with open(os.path.join(property_paths["data"], new_v_name+".json"), "w") as fp:
                        json.dump(data_variable, fp)
                else:
                    with open(os.path.join(property_paths["data"], data_variables[v]+".json"), "w") as fp:
                        json.dump(data_variable, fp)
                print(data_variable)
            if keep_prints:
                print(mystdout)
            tmp_keywords = keywords
            if type(keywords) == str:
                tmp_keywords = [keywords, ]
            print_split = mystdout.split(delimiter)
            butlered_lines = ""
            for kwd in tmp_keywords:
                for prnt in print_split:
                    if kwd in prnt:
                        butlered_lines += prnt + ("\n" if add_new_line else "")
            # butlered_lines goes to exp_{}/meas_prop/log.txt
            with open(property_log, "w") as fp:
                fp.write(butlered_lines)
            return res
        return wrapper
    return decorated


butler.session_exists = False
butler.session_paths = dict()
butler.property_setup = dict()


def add_quantity_setup(path_to_setup, setup_dict):
    with open(path_to_setup, "w") as fp:
        json.dump(setup_dict, fp)


def add_exp_setup(quantity, setup_dict):
    setup_path = butler.session_paths["setup"]
    with open(setup_path, "r") as fp:
        current_exp_setup = json.load(fp)
    with open(setup_path, "w") as fp:
        current_exp_setup[quantity] = setup_dict
        json.dump(current_exp_setup, fp)


def _update_internal_setup(setup_dict):  # atm only the last used setup for the given quantity
    setups_path = os.path.join(this_dir(), "setups")
    if not os.path.isdir(setups_path):
        butler.setups_folder = setups_path
        os.mkdir(setups_path)
    setups_path = os.path.join(setups_path, "setups.json")
    if not os.path.isfile(setups_path):
        with open(setups_path, "w") as fp:
            fp.write("{}")
    with open(setups_path, "r") as fp:
        current_exp_setup = json.load(fp)
    with open(setups_path, "w") as fp:
        current_exp_setup[get_time_string()] = setup_dict
        json.dump(current_exp_setup, fp)


# class BullshitClass:
#     def __init__(self):
#         self.bullshit_value = [1,2,3,4,5,6,7,8,9]
#
#     @butler("[INFO]", delimiter="\n", keep_prints=True, data_variables=("self.bullshit_value", ))
#     def multiply(self, a, b):
#         _setup = {"gripper": "2F85", "manipulator": "kinova lite 2"}
#         _meas = MeasObject("youngs_modulus", "continuous", {"mean": 500000, "std": 100000}, [1,5,8,5,2,7,5,1,3,8,7,1,5,8,85,1,5,8,8,4,12,65], 6)
#         print("this should only be in the top log")
#         print("[INFO] no thanks")
#         print("result: ", a*b)
#         # print(dir())
#         return _meas, a*b


if __name__ == "__main__":
    # print("dude1")
    all_vars = dir()
    bc = BullshitClass()
    c = bc.multiply(37, 20)
    c = bc.multiply(39, 20)
    # print(all_vars)
    # print(eval('andrej_meas').__dict__)
    print(eval("__file__"))



