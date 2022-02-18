import sys
import os
from io import StringIO
from datetime import datetime
import json
from random import random



# examine mystdout.getvalue()
print()
print()
# print("mystdout:", mystdout.getvalue())
print()


def print_callable(f):
    def decorated(*args, **kwargs):
        res = f(*args, **kwargs)
        print(res)
        return res
    return decorated


def cache_print(f, *args, **kwargs):
    """
    Save the return value of f & prints from this function in a tuple:: (return values, prints)
    :param f:
    :param args:
    :param kwargs:
    :return:
    """
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()

    ret = f(*args, **kwargs)

    sys.stdout = old_stdout
    return ret, mystdout.getvalue()


# class Data:
#     def __init__(self):


class Property:
    def __init__(self, name, unit=None):
        self.name = name
        self.log = 'log.txt'
        self.imgs = 'imgs/'
        self.figs = 'figs/'
        self.data = 'data/'


class TopFolder:
    def __init__(self, id: int, properties: list[str]):
        self.name = "exp-{}".format(id)
        # for prop in properties:
        #     self.__dict__[prop] =


DirectoryStructure = {
    "name":
        "exp_{}",
    "structure":
        {
            "log": "log.txt",
            "setup": "setup.json",
        }
}

PropertyStructure = {
    "name": "{}",
    "structure": {
        "log": "log.txt",
        "imgs": "imgs/",
        "figs": "figs/",
        "data": {
            "name":
                "data/",
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
    print(lowest_num)
    new_exp_path = os.path.join(parent_dir, DirectoryStructure["name"].format(lowest_num))
    new_log_path = os.path.join(new_exp_path, DirectoryStructure["structure"]["log"])
    new_setup_json_path = os.path.join(new_exp_path, "setup.json")

    # create dirs & files
    os.mkdir(new_exp_path)
    with open(new_log_path, "w") as f:
        pass
    with open(new_setup_json_path, "w") as f:
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
    new_dirs = [new_prop_dir, imgs_dir, figs_dir, data_dir]
    new_files = [log_file, meas_file]
    for d in new_dirs:
        os.mkdir(d)
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
           meas_object_var_name="_meas", measured_object_type=MeasObject):
    assert type(meas_object_var_name) == str, "measured object variable name must be string! & Only one per function"
    assert type(keywords) == str or type(keywords) == list, "keywords must be of type str or list[str]"

    if new_session or not butler.session_exists:
        butler.session_paths = create_directory_tree_for_session(parent_dir=session_parent_dir)
    else:
        pass

    def decorated(f):
        def wrapper(*args, **kwargs):
            # variables exist after this function:
            res, mystdout = cache_print(f, *args, **kwargs)

            """general log"""
            with open(butler.session_paths["log"], "w") as fp:
                # print(type(mystdout), mystdout)
                fp.write(mystdout)

            """single property logs, etc."""
            """meas_prop, meas_type, params, values, meas_ID"""
            new_measurement = eval(meas_object_var_name).__dict__
            measured_property = new_measurement["meas_prop"]
            property_paths = create_property_entry(butler.session_paths["exp"], new_measurement)
            # into property_paths["log"] should go the prints caught by `keywords`
            property_log = property_paths["log"]

            if keep_prints:
                print(mystdout)
            tmp_keywords = keywords
            if type(keywords) == str:
                tmp_keywords = [keywords, ]
            print_split = mystdout.split(delimiter)
            time_string = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
            butlered_lines = ""
            for kwd in tmp_keywords:
                for prnt in print_split:
                    if kwd in prnt:
                        butlered_lines += prnt + ("\n" if add_new_line else "")
            # butlered_lines goes to exp_{}/meas_prop/log.txt
            with open(property_log, "w") as fp:
                fp.write(butlered_lines)
            # with open("session_%s.txt" % time_string, "a") as fp:
            #     # print("SESSION RECORDING")
            #     fp.write(butlered_lines)
            return res
        return wrapper
    return decorated


butler.session_exists = False
butler.session_paths = ""


@butler("[INFO]", delimiter="\n", keep_prints=False, meas_object_var_name="andrej_meas")
def multiply(a, b):
    print("this should only be in the top log")
    print("[INFO] YAYAYAYYAYAYAYAYAYYAYAYAYAYYAYAYAYAYYAYAYYAYAYYAYAYYAYAYAYYAY")
    print("this should only be in the top log")
    print("[INFO] YAYAYAYYAYAYAYAYAYYAYAYAYAYYAYAYAYAYYAYAYYAYAYYAYAYYAYAYAYYAY")
    print("this should only be in the top log")
    print("[INFO] YAYAYAYYAYAYAYAYAYYAYAYAYAYYAYAYAYAYYAYAYYAYAYYAYAYYAYAYAYYAY")
    return a*b


if __name__ == "__main__":
    print("dude1")
    all_vars = dir()
    andrej_meas = MeasObject("andrejprop", "andrej", "andrej2", "andrej3", 6549547974)
    c = multiply(37, 20)
    print(all_vars)
    print(eval('andrej_meas').__dict__)
    print(eval("__file__"))
    # create_directory_tree_for_session(os.getcwd())



