import sys
import os
from io import StringIO
from datetime import datetime
import json


# def get_next_number(in_str):
#     for i in range(len(in_str)):
#


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
            "setup": "setup.json",
            "timestamp": "time_stamp{}"
        }
}

PropertyStructure = {
    "name": "{}",
    "structure": {
        "log": "log.txt",
        "imgs": "imgs",
        "figs": "figs",
        "setup": "setup.json",
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


def get_free_num(str_in: str):
    split_str = str_in.split("_")
    if os.path.isfile(str_in):
        return 0
    if len(split_str) != 2:
        return 0
    return int(split_str[1])+1


def create_directory_tree_for_session(parent_dir: str):
    existing_directories = os.listdir()
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
        fp.write("{}")
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
    new_prop_dir = j(parent_dir, meas_dict["meas_prop"])
    imgs_dir = j(new_prop_dir, prop_struct["imgs"])
    figs_dir = j(new_prop_dir, prop_struct["figs"])
    data_dir = j(new_prop_dir, prop_struct["data"]["name"])
    log_file = j(new_prop_dir, prop_struct["log"])
    meas_file = j(data_dir, prop_struct["data"]["structure"]["meas"]["name"])
    setup_file = j(new_prop_dir, prop_struct["setup"])
    new_dirs = [new_prop_dir, imgs_dir, figs_dir, data_dir]
    new_files = [log_file, meas_file, setup_file]
    for d in new_dirs:
        new_dir_name = d
        # if os.path.isdir(d):

            # new_dir_name = d +
        os.mkdir(new_dir_name)
    for f in new_files:
        with open(f, "w") as f:
            pass
    with open(meas_file, "w") as f:
        json.dump(meas_dict, f)
    ret = dict()
    ret["property"] = new_prop_dir
    ret["imgs"] = imgs_dir
    ret["figs"] = figs_dir
    ret["data"] = data_dir
    ret["setup"] = setup_file
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
           keep_prints=True,
           new_session=False, session_parent_dir=os.getcwd(),
           meas_object_var_name="_meas", measured_object_type=MeasObject,
           meas_setup="_setup"):
    assert type(meas_object_var_name) == str, "measured object variable name must be string! & Only one per function"
    assert type(keywords) == str or type(keywords) == list, "keywords must be of type str or list[str]"

    def decorated(f):
        def wrapper(*args, **kwargs):
            if new_session or not butler.session_exists:
                butler.session_paths = create_directory_tree_for_session(parent_dir=session_parent_dir)
            else:
                pass

            # variables exist after this function:
            res, mystdout = cache_print(f, *args, **kwargs)

            """general log"""
            with open(butler.session_paths["log"], "w") as fp:
                # print(type(mystdout), mystdout)
                fp.write(mystdout)
            setup_dict = eval("butler."+meas_setup)
            if not type(setup_dict) == dict:
                setup_dict = setup_dict.__dict__

            """single property logs, etc."""
            """meas_prop, meas_type, params, values, meas_ID"""
            # print(eval(meas_object_var_name))
            new_measurement = eval("butler."+meas_object_var_name).__dict__
            measured_property = new_measurement["meas_prop"]

            property_paths = create_property_entry(butler.session_paths["exp"], new_measurement)
            # into property_paths["log"] should go the prints caught by `keywords`
            property_log = property_paths["log"]

            add_quantity_setup(property_paths["setup"], setup_dict)
            add_exp_setup(measured_property, setup_dict)
            _update_internal_setup(measured_property, setup_dict)

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


def _update_internal_setup(quantity, setup_dict):  # atm only the last used setup for the given quantity
    butler.property_setup[quantity] = setup_dict
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
        get_time_string()
        current_exp_setup[quantity] = setup_dict
        json.dump(current_exp_setup, fp)


@butler("[INFO]", delimiter="\n", keep_prints=False, meas_object_var_name="andrej_meas", meas_setup="andrej_setup")
def multiply(a, b):
    # print(andrej_meas)
    butler.andrej_setup = {"gripper": "2F85", "manipulator": "kinova lite 2"}
    butler.andrej_meas = MeasObject("andrejprop", "andrej", "andrej2", "andrej3", 6549547974)
    print("this should only be in the top log")
    print("[INFO] no thanks")
    print("result: ", a*b)
    return a*b


if __name__ == "__main__":
    # print("dude1")
    all_vars = dir()
    c = multiply(37, 20)
    c = multiply(39, 20)
    # print(all_vars)
    # print(eval('andrej_meas').__dict__)
    print(eval("__file__"))



