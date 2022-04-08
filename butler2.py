from __future__ import print_function, division

import sys
import os
from io import BytesIO as StringIO
from datetime import datetime
import json
import numpy as np
import re
from copy import deepcopy
import shutil

__all__ = ["dump_numpy_proof", "numpy_to_native", "PropertyMeasurement", "butler"]
_real_std_out = None


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


class CustomStringIO(StringIO):
    def write(self, data):
        _real_std_out.write(data)
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
    global _real_std_out
    _real_std_out = sys.stdout
    sys.stdout = mystdout = CustomStringIO()
    ret = f(*args, **kwargs)

    sys.stdout = _real_std_out
    return ret, mystdout.getvalue()


DirectoryStructure = {
    "name":
        "experiment_{}",
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
                            "name": "measurement.json",
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


def get_set(the_set, the_dict):
    for item in the_set:
        the_item = the_dict.get(item)
        if the_item is not None:
            return the_item
    return None


class Butler:
    session_exists = False
    session_paths = None
    property_setup = dict()
    context = list()
    counter = 0
    property_object_property_name = {"prop", "name", "property_name", "property", "meas_prop", "meas_name", "measured_property", "measurement_property", "measured_name", "measurement_name"}
    tmp_img_files = ()
    tmp_fig_files = ()
    tmp_data_files = ()

    @staticmethod
    def __call__(keywords=(),
                 keep_keywords=True,
                 setup_file="setup.json",
                 delimiter="\n",
                 add_new_line=True,
                 read_return=True,
                 session_parent_dir=os.path.dirname(__file__),
                 output_variable_name="",
                 data_variables=(),
                 img_files=(),
                 fig_files=(),
                 data_files=(),
                 ignore_colours=True,
                 create_new_exp_on_run=False):
        assert type(output_variable_name) == str, "measured object variable name must be string! & Only one per function"

        assert type(keywords) == str or type(keywords) == list or type(keywords) == tuple, \
            "keywords must be of type str or list[str]"

        try:
            with open(setup_file, "r") as fp:
                Butler.setup = json.load(fp)
        except IOError as e:
            raise IOError(
                "\n1. setup.json is not located in session_parent_dir=" + session_parent_dir +
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
            Butler.session_paths = Butler._create_directory_tree_for_session(parent_dir=session_parent_dir,
                                                                             setup=Butler.setup)

        def decorated(f):
            def wrapper(*args, **kwargs):
                if create_new_exp_on_run:
                    Butler.session_paths = Butler._create_directory_tree_for_session(parent_dir=session_parent_dir,
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

                if read_return:
                    if type(res) == tuple:
                        output_variable = res[0]
                    else:
                        output_variable = res
                else:
                    output_variable = eval(output_variable_name)

                if type(output_variable) == dict:
                    new_measurement = output_variable
                elif isinstance(output_variable, object):
                    # elif type(output_variable) == instance:
                    # print("type(output_variable):", type(output_variable).__dict__)
                    new_measurement = output_variable.__dict__
                    # print("outout var is a CLASSSS!!!!")
                else:
                    raise TypeError(
                        "for return value or specified output_variable is not of type [dict, PropertyMeasurement]"
                    )

                # print("new measurement: ", new_measurement)
                # exit(1)
                property_paths = Butler._create_property_entry(Butler.session_paths["exp"], new_measurement)
                if len(fig_files) > 0:
                    for fig_file in fig_files:
                        shutil.copy2(fig_file, property_paths["figs"])

                if len(img_files) > 0:
                    for img_file in img_files:
                        shutil.copy2(img_file, property_paths["imgs"])

                if len(data_files) > 0:
                    for data_file in data_files:
                        shutil.copy2(data_file, property_paths["data"])

                tmp_img_files = Butler.get_tmp_files("imgs")
                if len(tmp_img_files) > 0:
                    for tmp_file in tmp_img_files:
                        shutil.copy2(tmp_file, property_paths["imgs"])

                tmp_fig_files = Butler.get_tmp_files("figs")
                if len(tmp_fig_files) > 0:
                    for tmp_file in tmp_fig_files:
                        shutil.copy2(tmp_file, property_paths["figs"])

                tmp_data_files = Butler.get_tmp_files("data")
                if len(tmp_data_files) > 0:
                    for tmp_file in tmp_data_files:
                        shutil.copy2(tmp_file, property_paths["data"])

                # the prints containing `keywords` go into property_paths["log"]
                property_log = property_paths["log"]

                Butler._update_internal_setup(Butler.setup)

                """
                data variables should know where they come from:
                data_vars = [{"var_name": {"values": var_name, "source": "setup_el_name"-must be in setup values}}]
                """
                data_variables_listified = data_variables
                if type(data_variables) not in {np.ndarray, tuple, list}:
                    if type(data_variables) == dict:
                        data_variables_listified = (data_variables,)
                    else:
                        raise TypeError(
                            "data_variables is not of type [iterable[dict], dict]: " +
                            str(type(data_variables_listified))
                        )
                for varname in data_variables_listified:
                    new_v_name = varname.replace("self.", "")
                    if "self." in varname:
                        data_variable = args[0].__dict__[new_v_name]  # for class functions `func(self, arg1)`
                    else:
                        data_variable = eval(new_v_name)
                    assert "values" in data_variable, \
                        "\"values\" key not in variable " + str(varname) + ": " + str(data_variable)
                    assert "source" in data_variable, \
                        "\"source\" key not in variable " + str(varname) + ": " + str(data_variable)
                    with open(os.path.join(property_paths["data"], new_v_name + ".json"), "w") as fp:
                        dump_numpy_proof(data_variable, fp)
                object_context = Butler._pop_object_context()
                if object_context:
                    with open(os.path.join(property_paths["data"], "object_context.json"), "w") as fp:
                        dump_numpy_proof(object_context, fp)

                tmp_keywords = keywords
                if type(keywords) == str:
                    tmp_keywords = (keywords,)
                print_split = processed_std_out.split(delimiter)
                butlered_lines = ""
                for kwd in tmp_keywords:
                    for prnt in print_split:
                        if kwd in prnt:
                            if keep_keywords:
                                butlered_lines += prnt + ("\n" if add_new_line else "")
                            else:
                                butlered_lines += prnt.replace(kwd, "") + ("\n" if add_new_line else "")

                # butlered_lines goes to experiment_{}/meas_prop/log.txt
                with open(property_log, "w") as fp:
                    fp.write(butlered_lines)
                return res

            return wrapper

        return decorated

    @staticmethod
    def _get_free_num(str_in):
        split_str = str_in.split("_")
        if os.path.isfile(str_in):
            return 0
        if "experiment_" in str_in:
            return int(split_str[-1]) + 1
        else:
            return 0

    @staticmethod
    def _create_directory_tree_for_session(parent_dir, setup):
        existing_directories = os.listdir(os.path.dirname(__file__))
        # get the lowest unused number that isn't lower than any other number in this dir
        lowest_num = max(map(Butler._get_free_num, [os.path.join(os.path.dirname(__file__), exdir) for exdir in existing_directories]))

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
    def _create_property_entry(parent_dir, meas_dict):
        # print("BULTER: CREATING PROPERTY ENTRYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY")
        j = os.path.join
        prop_struct = PropertyStructure["structure"]

        ls_exp = os.listdir(parent_dir)
        next_index = 0
        for n in ls_exp:
            # print(get_set(Butler.property_object_property_name, meas_dict), "in", n, ":", get_set(Butler.property_object_property_name, meas_dict) in n)
            if get_set(Butler.property_object_property_name, meas_dict) in n:  # "mass" in "mass_0"
                next_index = max(int(n.split("_")[-1]) + 1, next_index)

        new_prop_dir = j(parent_dir, get_set(Butler.property_object_property_name, meas_dict) + "_" + str(next_index))
        imgs_dir = j(new_prop_dir, prop_struct["imgs"])
        figs_dir = j(new_prop_dir, prop_struct["figs"])
        data_dir = j(new_prop_dir, prop_struct["data"]["name"])
        log_file = j(new_prop_dir, prop_struct["log"])
        meas_file = j(data_dir, prop_struct["data"]["structure"]["meas"]["name"])
        new_dirs = [new_prop_dir, imgs_dir, figs_dir, data_dir]
        new_files = [log_file, meas_file]
        for d in new_dirs:
            new_dir_name = d
            # new_index = 0
            # while os.path.isdir(new_dir_name):  # idk why but just in case the directory exists here
            #     new_split = new_dir_name.split("_")
            #     try:
            #         new_index = int(new_split[-1]) + 1
            #     except:
            #         new_index = 0
            #     new_name = ""
            #     for _ in range(len(new_split) - 1):
            #         new_name += new_split[_] + "_"
            #     new_dir_name = new_name + str(new_index)
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
    def add_object_context(context, override_recommendation=False):
        assert type(context) == dict, "object context must be in the format {key: value for (key, value) in key_values}"
        context_values = context.values()
        context_keys = context.keys()
        assert sum(map(lambda x: type(x) == str, context_keys)) == \
               sum(map(lambda x: type(x) == str, context_values)) == len(context_values), \
               "context dictionary must have string keys and values: "+str(context)

        if not override_recommendation:
            if not ("maker" in context or
                    "common_name" in context or
                    "dataset" in context or
                    ("dataset" in context and "dataset_id" in context)):
                raise ValueError("Butler: It is recommended to set the object context as "
                      "\"maker\" or \"common_name\" or (\"dataset\"  (and \"dataset_id\" optional))")
        Butler.context.append(context)

    @staticmethod
    def _pop_object_context():
        print(Butler.context)
        if len(Butler.context) != 0:
            ret = Butler.context.pop(0)
            print(Butler.context)
            return ret
        else:
            return None

    @staticmethod
    def add_tmp_files(file_paths, tmp_file_folder):
        """Adds files to be copied to the folder: property/[data, imgs, figs] when the function decorated by `@butler` is called.

        Parameters
        ----------
        file_paths : list[str]
            The files to be copied to tmp_file_folder
        tmp_file_folder : str
            One of ["data", "imgs", "figs"]. The `experiment_i/property_j` subfolder into which the `file_paths` files are to be copied.

        """
        assert tmp_file_folder in {"data", "figs", "imgs"}, "folder has to be one of {\"data\", \"figs\", \"imgs\"}"
        valid_file_paths = file_paths
        if type(valid_file_paths) not in {list, tuple}:
            valid_file_paths = (valid_file_paths, )
        if tmp_file_folder == "data":
            Butler.tmp_data_files = file_paths
        if tmp_file_folder == "figs":
            Butler.tmp_fig_files = file_paths
        if tmp_file_folder == "imgs":
            Butler.tmp_img_files = file_paths

    @staticmethod
    def get_tmp_files(figs_imgs_data):
        if figs_imgs_data == "figs":
            ret = Butler.tmp_fig_files
            Butler.tmp_fig_files = ()
            return ret
        if figs_imgs_data == "figs":
            ret = Butler.tmp_fig_files
            Butler.tmp_fig_files = ()
            return ret
        if figs_imgs_data == "data":
            ret = Butler.tmp_data_files
            Butler.tmp_data_files = ()
            return ret


butler = Butler()  # to make `from butler2 import butler` possible and to have its fields recognized by IDEs


class PropertyMeasurement:
    """
    "density", "continuous", {"mean": 100, "sigma": 10}, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], meas_ID=1
    """

    def __init__(self, property_name=None, measurement_type=None, parameters=None, units=None,
                 grasp=None, values=None, repository=None,
                 other=None, other_file=None, **kwargs):
        self.property_name = property_name  # eg mass, elasticity, vision, sound
        self.measurement_type = measurement_type  # continuous, discrete
        self.parameters = parameters  #
        self.units = units
        self.grasp = grasp
        self.values = values
        self.repository = repository
        self.other = other
        self.other_file = other_file
        for k in kwargs:
            exec("self."+k+"="+str(kwargs[k]))

    def __repr__(self):
        rep = ""
        if hasattr(self, "meas_ID"):
            rep += "------ID:{}------\n".format(self.meas_ID)
        rep += "Property: {} of type: {}\n".format(self.property_name, self.measurement_type)
        rep += "Params: {}\n".format(self.parameters)
        rep += "Some Values: {}...{}\n".format(self.values[0:5], self.values[-5:])
        if self.other is not None:
            rep += "Other: {}\n".format(self.other)
        if self.other_file is not None:
            rep += "Other file: {}\n".format(self.other_file)

        return rep


if __name__ == "__main__":
    class MeasObject:
        """
        "density", "continuous", {"mean": 100, "sigma": 10}, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], meas_ID=1
        """

        def __init__(self, meas_prop, meas_type, params, values, units, meas_ID):
            self.meas_prop = meas_prop  # eg mass, elasticity, vision, sound
            self.meas_type = meas_type  # continuous, discrete
            self.params = params  #
            self.values = values
            self.units = units
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
            self.test_value1 = {"values": {"position": [1, 2, 3, 4, 5, 6, 7, 8, 9]}, "source": "gripper_name"}
            self.test_value2 = {"values": [9, 8, 7, 6, 5, 6, 7, 8, 9], "source": "gripper_name"}
            self.test_value3 = {"values": {"current": [1, 2, 3, 4, 5, 6, 7, 8, 9]}, "source": "arm_name"}

        # @butler(keywords="[INFO]", delimiter="\n", data_variables=("self.test_value2", "self.test_value3"), create_new_exp_on_run=True)
        # def multiply(self, a, b):
        #     _meas = PropertyMeasurement("elasticity", "continuous", {"mean": 500000, "std": 100000},
        #                                 grasp={"position": [0.1, 0.2, 0.3], "rotation": [0.5, 0.9, 0.7], "grasped": True},
        #                                 values=self.test_value1, units="Pa", repository="http://www.github.com", meas_ID=6)
        #     print("this should only be in the top log")
        #     print("[INFO] no thanks")
        #
        #     stringlol = "\033[1;31m Sample Text \033[0m"
        #     print(stringlol)
        #     print("result: ", a * b)
        #     # print(dir())
        #     Butler.add_object_context({"maker": "coca_cola"}, override_recommendation=False)
        #     return _meas, a * b

        @butler(keywords="[INFO]", delimiter="\n", keep_keywords=False, data_variables=("self.test_value2",),
                create_new_exp_on_run=True)
        def divide(self, a, b):
            _meas = PropertyMeasurement(property_name="object_category",
                                        measurement_type="categorical",
                                        parameters={"cat1": 0.5, "cat2": 0.3, "cat3": 0.2},
                                        meas_ID=6)
            print("this should only be in the top log")
            print("[INFO] divide baby [INFO]")
            stringlol = "\033[1;31m Sample Text \033[0m"

            print(stringlol)
            print("result: ", a / b)
            # print(dir())
            Butler.add_object_context({"common_name": "yellow_sponge"}, override_recommendation=False)
            return _meas, a / b


    # print(this_dir())
    import shutil
    for _ in os.listdir(this_dir()):
        if os.path.isdir(_):
            rematch = re.findall(pattern=r"experiment_\d", string=_)
            if len(rematch) == 1:
                shutil.rmtree(_)
    # print(os.listdir(this_dir()))
    all_vars = dir()
    bc = TestClass()
    # c = bc.multiply(39, 20)
    d = bc.divide(40, 20)
    print(eval("__file__"))
