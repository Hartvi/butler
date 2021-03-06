from __future__ import print_function, division

import sys
import os
from os.path import join
if sys.version_info[0] == 2:
    from io import BytesIO
else:
    from io import StringIO as BytesIO
import json
import numpy as np
import re
import shutil

from utils import dump_numpy_proof, get_time_string
import config

# __all__ = ["PropertyMeasurement", "logger"]
_real_std_out = None  # type: BytesIO


def format_data_variables(data_vars):
    """
    Removes unused "sensors" from the data variables.

    Parameters
    ----------
    data_vars : tuple[dict]
        Tuple of data variables formatted like a dictionary {"sensor": {"quantity": values}}
    """
    ret = dict()
    for v in data_vars:  # {"sensor": {"quantity": values}}
        for s in v:  # "sensor"
            sensor_is_used = False
            if v[s] is None:
                continue
            for q in v[s]:  # "quantity"
                used_sum = 0
                if v[s][q] is not None:
                    used_sum += 1
                try:
                    if len(v[s][q]) != 0:
                        used_sum += 1
                except:
                    pass
                if used_sum > 1:
                    sensor_is_used = True
            if sensor_is_used:
                ret[s] = v[s]
    return ret


class CustomBytesIO(BytesIO):
    """BytesIO pipe that copies all prints into itself
    """
    def write(self, data):
        _real_std_out.write(data)
        # real_std_out.write("\n"+str(super(CustomBytesIO, self).__dict__))
        super(CustomBytesIO, self).write(data)  # this is writing into BytesIO, so it might need `data.encode()`


def this_dir():
    """Returns the directory of the current python file

    Returns
    -------
    str
        Current parent dir of this file
    """
    real_path = os.path.realpath(__file__)
    dir_path = os.path.dirname(real_path)
    return dir_path


def cache_print(f, *args, **kwargs):
    """Save the return value of function `f` & its print outputs

    Parameters
    ----------
    f : function
        Function whose prints you want saved.
    args : any
        Classical *args.
    kwargs : dict
        Classical **kwargs.

    Returns
    -------
    tuple
        tuple of (function_return, stdout)
    """
    global _real_std_out
    _real_std_out = sys.stdout
    sys.stdout = mystdout = CustomBytesIO()
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
    """Butler collects and organizes experiment data into folders while the experiment is running.

    Parameters
    ----------
    keywords : str or list or tuple
        List of keywords whose lines will be extracted when printed
    keep_keywords : bool
        Whether to also save the keywords with the rest of the print line
    setup_file : str
        Path to the json containing the setup mappings. E.g. {"gripper": "robotiq 2f85", ...}
    session_parent_dir : str
        Directory where to save the experiments; default is the butler.py directory
    output_variable_name : str
        The string name of the variable that contains the data that is otherwise returned by the decorated function. Has to be visible in the scope where the decorated function is called. E.g. `self.data_var` or `just_data_var`.
    data_variables : list or tuple or str or dict[str, list or tuple or np.ndarray or str]
        Sensor output variables. Format: {"source_sensor_name": {"quantity (e.g. postiion)": [list, of, values], ...}, ...}
    img_files : list[str] or tuple[str]
        List of file paths that will be copied to `experiment_i/property_j/imgs` every time the function is run.
    fig_files : list[str] or tuple[str]
        List of file paths that will be copied to `experiment_i/property_j/figs` every time the function is run.
    data_files : list[str] or tuple[str]
        List of file paths that will be copied to `experiment_i/property_j/data` every time the function is run.
    ignore_colours : bool
        Whether to ignore the special colour characters; in regex: "\033\[\d+](;\d+)?m"
    create_new_exp_on_run : bool
        Whether to create a new experiment_i folder on every run of the function.

    """
    session_exists = False
    session_paths = None
    property_setup = dict()
    context = list()
    counter = 0
    # TODO: regex dict getting \/
    property_object_property_name = {"prop", "name", "property_name", "property", "meas_prop", "meas_name", "measured_property", "measurement_property", "measured_name", "measurement_name"}
    tmp_img_files = ()
    tmp_fig_files = ()
    tmp_data_files = ()
    tmp_img_target_names = ()
    tmp_fig_target_names = ()
    tmp_data_target_names = ()
    file_mappings = dict()
    png_path = None
    img_files = ()
    fig_files = ()
    data_files = ()
    setup = None

    def __init__(self,
                 keywords=(),
                 keep_keywords=True,
                 setup_file="setup.json",
                 session_parent_dir=config.experiment_directory,
                 output_variable_name="",
                 data_variables=(),
                 img_files=(),
                 fig_files=(),
                 data_files=(),
                 ignore_colours=True,
                 create_new_exp_on_run=False):

        """Butler collects and organizes experiment data into folders while the experiment is running.

        Parameters
        ----------
        keywords : str list or tuple
            List of keywords whose lines will be extracted when printed
        keep_keywords : bool
            Whether to also save the keywords with the rest of the print line
        setup_file : str
            Path to the json containing the setup mappings. E.g. {"gripper": "robotiq_2f85", ...}
        session_parent_dir : str
            Directory where to save the experiments; default is the butler.py directory
        output_variable_name : str
            The string name of the variable that contains the data that is otherwise returned by the decorated function. Has to be visible in the scope where the decorated function is called. E.g. `self.data_var` or `just_data_var`.
        data_variables : list or tuple or str or dict[str, list or tuple or np.ndarray or str]
            Sensor output variables. Format: {"source_sensor_name": {"quantity (e.g. postiion)": [list, of, values], ...}, ...}
        img_files : list[str] or tuple[str]
            List of file paths that will be copied to `experiment_i/property_j/imgs` every time the function is run.
        fig_files : list[str] or tuple[str]
            List of file paths that will be copied to `experiment_i/property_j/figs` every time the function is run.
        data_files : list[str] or tuple[str]
            List of file paths that will be copied to `experiment_i/property_j/data` every time the function is run.
        ignore_colours : bool
            Whether to ignore the special colour characters; in regex: "\033\[\d+(;\d+)?m"
        create_new_exp_on_run : bool
            Whether to create a new experiment_i folder on every run of the function.

        """
        assert type(output_variable_name) == str or output_variable_name is None,\
            "measured object variable name must be a string!"

        assert type(keywords) == str or type(keywords) == list or type(keywords) == tuple, \
            "keywords must be of type str or list[str]"

        self.keywords = keywords
        self.keep_keywords = keep_keywords
        self.setup_file = setup_file
        self.session_parent_dir = session_parent_dir
        self.output_variable_name = output_variable_name
        self.data_variables = data_variables
        self.img_files = img_files
        self.fig_files = fig_files
        self.data_files = data_files
        self.ignore_colours = ignore_colours
        self.create_new_exp_on_run = create_new_exp_on_run

        try:
            with open(setup_file, "r") as fp:
                self.setup = json.load(fp)
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
        if self.session_paths is None and not create_new_exp_on_run:
            self.session_paths = self._create_directory_tree_for_session()

    def __call__(self, f):

        def wrapper(*args, **kwargs):
            if self.create_new_exp_on_run:
                self.session_paths = self._create_directory_tree_for_session()
            res, captured_std_out = cache_print(f, *args, **kwargs)
            processed_std_out = captured_std_out

            if self.ignore_colours:
                processed_std_out = re.sub(r"\033\[\d+(;\d+)?m", "", captured_std_out)

            """general log"""
            with open(self.session_paths["log"], "a") as fp:
                fp.write(processed_std_out)

            """single property logs, etc."""
            """meas_prop, meas_type, params, values, meas_ID"""

            if self.output_variable_name is None:
                if type(res) == tuple:
                    output_variable = res[0]
                else:
                    output_variable = res
            else:
                output_variable = eval(self.output_variable_name)

            if type(output_variable) == dict:
                new_measurement = output_variable
            elif isinstance(output_variable, object):
                new_measurement = output_variable.__dict__
            else:
                raise TypeError(
                    "for return value or specified output_variable is not of type [dict, PropertyMeasurement]"
                )

            property_paths = self._create_property_entry(new_measurement)
            folder_names = ['fig', 'img', 'data']

            # save the provided tmp_files into the property's imgs/figs/data folders
            for n in folder_names:
                _files = eval("Butler."+n+"_files")
                plural_n = n+("s" if len(n) == 3 else "")
                property_path = property_paths[plural_n]
                if len(_files) > 0:
                    for _file in eval(n+"_files"):
                        shutil.copy2(_file, property_path)

                butler_tmp_n = "Butler.tmp_" + n
                tmp_length = len(eval(butler_tmp_n+"_files"))  # e.g. tmp_img_files, tmp_data_files, tmp_fig_files
                for i in range(tmp_length):
                    print("target path:", join(property_path, eval(butler_tmp_n+"_target_names[i]")))
                    target_path = join(property_path, eval(butler_tmp_n+"_target_names[i]"))
                    butler_tmp_n_files = butler_tmp_n+"_files[i]"
                    eval_butler_tmp_n_files = eval(butler_tmp_n_files)
                    shutil.copy2(eval_butler_tmp_n_files, target_path)
                    Butler.file_mappings[eval_butler_tmp_n_files] = target_path

            if Butler.png_path is not None:
                shutil.copy2(Butler.png_path, join(property_paths["data"], "img.png"))
            Butler.png_path = None

            # for some reason having this in a separate method doesn't register
            Butler.tmp_data_files = ()
            Butler.tmp_fig_files = ()
            Butler.tmp_img_files = ()

            # the prints containing `keywords` go into property_paths["log"]
            property_log = property_paths["log"]

            # data variables should know where they come from:
            # data_vars = [{"var_name": {"setup_el_name": "values"}}]
            data_variables_listified = self.data_variables
            if type(self.data_variables) not in {np.ndarray, tuple, list}:
                if type(self.data_variables) == str:
                    data_variables_listified = (self.data_variables, )
                else:
                    raise TypeError(
                        "data_variables is not of type str: " +
                        str(type(data_variables_listified))
                    )
            for var_name in data_variables_listified:
                new_v_name = var_name.replace("self.", "")
                if "self." in var_name:
                    # for class functions `func(self, arg1)` => args[0] = self
                    data_variable = args[0].__dict__[new_v_name]
                else:
                    data_variable = eval(new_v_name)
                with open(join(property_paths["data"], new_v_name + ".json"), "w") as fp:
                    dump_numpy_proof(data_variable, fp)
            object_context = Butler._pop_object_context()
            if object_context:
                with open(join(property_paths["data"], "object_context.json"), "w") as fp:
                    dump_numpy_proof(object_context, fp)

            tmp_keywords = self.keywords
            if type(self.keywords) == str:
                tmp_keywords = (self.keywords, )
            print_split = processed_std_out.split("\n")
            butlered_lines = ""
            for kwd in tmp_keywords:
                for prnt in print_split:
                    if kwd in prnt:
                        if self.keep_keywords:
                            butlered_lines += prnt + "\n"
                        else:
                            butlered_lines += prnt.replace(kwd, "") + "\n"

            # butlered_lines goes to experiment_{}/meas_prop/log.txt
            with open(property_log, "w") as fp:
                fp.write(butlered_lines)
            Butler.counter += 1
            return res

        return wrapper

    def _create_directory_tree_for_session(self):
        parent_dir, setup = self.session_parent_dir, self.setup
        existing_directories = os.listdir(os.path.dirname(__file__))
        # get the lowest unused number that isn't lower than any other number in this dir

        experiment_suffix = get_time_string()
        new_exp_path = join(parent_dir, DirectoryStructure["name"].format(experiment_suffix))
        new_log_path = join(new_exp_path, DirectoryStructure["structure"]["log"])
        new_setup_json_path = join(new_exp_path, "setup.json")
        new_time_stamp_path = join(new_exp_path,
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

    def _create_property_entry(self, meas_dict):
        exp_dir = self.session_paths["exp"]
        prop_struct = PropertyStructure["structure"]

        ls_exp = os.listdir(exp_dir)
        next_index = 0
        # print(meas_dict["meas_prop"])
        for n in ls_exp:
            # print(n, meas_dict["meas_prop"] in n)
            if get_set(Butler.property_object_property_name, meas_dict) in n:  # "mass" in "mass_0"
                next_index = max(next_index, int(n.split("_")[-1]) + 1)

        new_prop_dir = join(exp_dir, get_set(Butler.property_object_property_name, meas_dict) + "_" + str(next_index))
        imgs_dir = join(new_prop_dir, prop_struct["imgs"])
        figs_dir = join(new_prop_dir, prop_struct["figs"])
        data_dir = join(new_prop_dir, prop_struct["data"]["name"])
        log_file = join(new_prop_dir, prop_struct["log"])
        meas_file = join(data_dir, prop_struct["data"]["structure"]["meas"]["name"])
        new_dirs = [new_prop_dir, imgs_dir, figs_dir, data_dir]
        new_files = [log_file, meas_file]
        for d in new_dirs:
            new_dir_name = d
            os.mkdir(new_dir_name)
        for f in new_files:
            with open(f, "w") as f:  # touch
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
    def add_object_context(context, override_recommendation=False):
        """Adds the object's "maker", "common_name", "dataset", "dataset_id" for one run of the function. Call `Butler.add_object_context(context)` inside the decorated funtion.

        Parameters
        ----------
        context : dict[str, str]
            The object context. Format: {"maker": "ikea", "common_name": "hard_yellow_sponge", "dataset": "ycb"}. If "dataset_id" is present, "dataset" must also be present.
        override_recommendation : bool
            Whether to remove the constraint that the context keys have to be one of ["maker", "common_name", "dataset", "dataset_id".]

        """
        assert type(context) == dict, "object context must be in the format {key: value for (key, value) in key_values}"
        
        for i in range(len(context)):
            for c in context:
                if context[c] is None:
                    del context[c]
                    break
        
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
        # print(Butler.context)
        if len(Butler.context) != 0:
            ret = Butler.context.pop(0)
            print(Butler.context)
            return ret
        else:
            return None

    @staticmethod
    def add_tmp_files(file_paths, tmp_file_folder, target_names=None):
        """Adds files to be copied to the folder: property_j/[data, imgs, figs] when the function decorated by `@butler` is called.

        Parameters
        ----------
        file_paths : list[str] or str
            The files to be copied to tmp_file_folder.
        tmp_file_folder : str
            One of ["data", "imgs", "figs"]. The `experiment_i/property_j` subfolder into which the `file_paths` files are to be copied.
        target_names : list[str] or str
            The names that the `file_paths` names will be copied into. E.g. file_paths="/tmp/box.png", target_names="cheezit.png"

        """
        assert tmp_file_folder in {"data", "figs", "imgs"}, "folder has to be one of {\"data\", \"figs\", \"imgs\"}"
        if target_names is not None and type(target_names) != str and type(file_paths) != str:
            assert len(target_names) == len(file_paths), "`target_names` has to be the same length as the source `file_paths`"

        valid_file_paths = file_paths
        if type(valid_file_paths) not in {list, tuple}:
            valid_file_paths = (valid_file_paths, )

        # defaults to the actual file name
        if target_names is None:
            valid_target_names = list(map(os.path.basename, valid_file_paths))
        else:
            valid_target_names = target_names
        if type(valid_target_names) not in {list, tuple}:
            valid_target_names = (valid_target_names, )

        if tmp_file_folder == "data":
            Butler.tmp_data_files = valid_file_paths
            Butler.tmp_data_target_names = valid_target_names
        if tmp_file_folder == "figs":
            Butler.tmp_fig_files = valid_file_paths
            Butler.tmp_fig_target_names = valid_target_names
        if tmp_file_folder == "imgs":
            Butler.tmp_img_files = valid_file_paths
            Butler.tmp_img_target_names = valid_target_names
        # print("BUTLER: ADDED TMP FILES TO: ", tmp_file_folder, " FILES: ", file_paths)

    @staticmethod
    def add_measurement_png(png_path):
        """Adds the png image to be uploaded into the measurement["png"] slot

        Parameters
        ----------
        png_path : str
            Path to the png file as it is on the disk.
        """

        if not os.path.isfile(png_path):
            raise IOError("png_path is not a valid path: `"+str(png_path)+"`")
        if Butler.png_path is not None:
            raise ValueError("Butler.png_path is being set twice in the same function!!")
        Butler.png_path = png_path


# butler = Butler()  # to make `from butler import butler` possible and to have its fields recognized by IDEs
"""Butler collects and organizes experiment data into folders while the experiment is running.

Parameters
----------
keywords : list or tuple
    List of keywords whose lines will be extracted when printed
keep_keywords : bool
    Whether to also save the keywords with the rest of the print line
setup_file : str
    Path to the json containing the setup mappings. E.g. {"gripper": "robotiq 2f85", ...}
read_return : bool
    Whether to take the return value (or first element in return tuple) as the measurement output. When False, see `outpu_bariable_name` parameter.
session_parent_dir : str
    Directory where to save the experiments; default is the butler.py directory
output_variable_name : str
    The string name of the variable that contains the data that is otherwise returned by the decorated function. Has to be visible in the scope where the decorated function is called. E.g. `self.data_var` or `just_data_var`.
data_variables : dict[str, list or tuple or np.ndarray or str]
    Sensor output variables. Format: {"source_sensor_name": {"quantity (e.g. postiion)": [list, of, values], ...}, ...}
img_files : list[str] or tuple[str]
    List of file paths that will be copied to `experiment_i/property_j/imgs` every time the function is run.
fig_files : list[str] or tuple[str]
    List of file paths that will be copied to `experiment_i/property_j/figs` every time the function is run.
data_files : list[str] or tuple[str]
    List of file paths that will be copied to `experiment_i/property_j/datas` every time the function is run.
ignore_colours : bool
    Whether to ignore the special colour characters; in regex: "\033\[\d+(;\d+)?m"
create_new_exp_on_run : bool
    Whether to create a new experiment_i folder on every run of the function.

"""


class PropertyMeasurement:

    def __init__(self, property_name=None, measurement_type=None, parameters=None, units=None,
                 grasp=None, values=None, repository=None,
                 other=None, other_file=None, **kwargs):
        self.property_name = property_name  # e.g. mass, elasticity, vision, sound
        self.measurement_type = measurement_type  # continuous, discrete
        self.parameters = parameters  #
        self.units = units
        self.grasp = grasp
        self.values = values
        self.repository = repository
        self.other = other
        self.other_file = other_file
        for k in kwargs:
            exec("self."+k+"="+str(("\""+kwargs[k]+"\"") if isinstance(kwargs[k], str) else kwargs[k]))

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
    class TestClass:
        def __init__(self):
            self.test_value1 = {"gripper_name": {"position": [1, 2, 3, 4, 5, 6, 7, 8, 9]}}
            self.test_value2 = {"gripper_name": {"values": [9, 8, 7, 6, 5, 6, 7, 8, 9]}}
            self.test_value3 = {"arm_name": {"current": [1, 2, 3, 4, 5, 6, 7, 8, 9]}}
            self.test_value4 = {"camera": {"point_cloud": "pointcloud.png"}}
            self.data_variables = {}

        @Butler(keywords="[INFO]",
                keep_keywords=False,
                data_variables=("self.data_variables", ),
                create_new_exp_on_run=True, setup_file=r"../setup.json")
        def divide(self, a, b):
            _meas = PropertyMeasurement(meas_prop="object_category",
                                        meas_type="continuous",  # "categorical",
                                        params={"mean": 20.2, "std": 5.1, "units": "kg", "name": "x"},
                                        meas_ID=6)
            print("this is in the top log")
            print("[INFO] this is in the property log")

            Butler.add_object_context({"common_name": "ycb_cup", "dataset_id": "65-f_cup", "dataset": "ycb", "maker": "sample_company"})
            for k in self.test_value4:
                self.data_variables[k] = self.test_value4[k]
            Butler.add_tmp_files(r"../unused/tests/setup_cropped.png", "data", "pointcloud.png")
            Butler.add_measurement_png(r"../unused/tests/setup_cropped.png")

            _meas.gripper_pose = {"position": [0.1, 0.2, 0.3], "rotation": [0.5, 0.8, 3.14], "grasped": True}
            _meas.object_pose = {"position": [0.3, 0.2, 0.1], "rotation": [3.0, 0.8, 3.14]}
            return _meas, a / b


    bc = TestClass()
    d = bc.divide(40, 20)
