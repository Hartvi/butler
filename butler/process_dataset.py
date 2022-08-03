import json
import re
import numpy as np
import os

import config

class DataUnit:
    sensor = ""  # type: str
    measurement_parameters = dict()  # type: dict
    sensor_data = dict()  # type: dict
    measured_object = dict()  # type: dict


class DataSet:
    data_loaders = list()  # type: list


top_dict = {}
#
# measurement = {}
# object_instance = {}
# setup = {}
# sensor_outputs = {}
# grasp = {}
# gripper_pose = {}
# object_pose = {}
#
# measurement["object_instance"] = object_instance
# measurement["setup"] = setup
# measurement["sensor_outputs"] = sensor_outputs
# measurement["grasp"] = grasp
# measurement["gripper_pose"] = gripper_pose
# measurement["object_pose"] = object_pose
#
# entry = {}
# values = {}
# entry["values"] = values
#
# top_dict["measurement"] = measurement
# top_dict["entry"] = entry


def register_get_data_functions(*args):
    for f in args:
        # data functions should return:
        # {
        #   "sensor": "sensor_name",
        #   "measurement_parameters": {
        #     "param1": "value1",
        #     ...
        #   },
        #   "sensor_data": {
        #     "quantity1": list or file path,
        #     ...
        #   },
        #   "measured_object": {
        #     "dataset": abc,
        #     "dataset_id": cba,
        #     "maker": xyz,
        #     "common_name": zyx,
        #     "other": "json string"
        #   }
        # }
        pass


def process_rg6_type(file_name, has_object_line=True, selected_data_columns=np.array([1, 2]), printable=False):
    """
    // object={obj_name}
    //prop1 prop2 ...
    """
    # object_name
    with open(file_name, "r") as f:
        if has_object_line:
            object_line = f.readline()
            lll = re.search(r"object=\s*[^\s]+", object_line)
            object_name = lll.group().replace(" ", "").replace("object=", "")
            # print("object_name", object_name)

        value_line = f.readline()
        # remove spaces, remove slashes, remove newline
        value_names = list(filter(lambda x: len(x) != 0, value_line.replace("/", "").replace("\n", "").split(" ")))
        # print("value_names", value_names)

        data_lines = list(map(lambda x: x.replace("\n", "").split(), f.readlines()))
        # i guess this is how far i go without numpy
        num_lines = len(data_lines)
        assert num_lines != 0, "The data must have at least one row! File: "+file_name
        data_columns = np.transpose(data_lines)

        selected_data = data_columns[selected_data_columns]
        # print("data_lines", np.shape(data_lines))
        # print("data_columns", np.shape(data_columns))
        # print(data_columns)
        # print("selected_data", selected_data)
        data_dict = {}
        for k,i in enumerate(selected_data_columns):
            data_dict[value_names[i]] = np.array(selected_data[k])
            if not printable:
                data_dict[value_names[i]] = data_dict[value_names[i]].tolist()
        # print(data_dict.keys())
        # old_object_str = lll.group()
        # while object_str != old_object_str:
        #     old_object_str = object_str
        #     object_str = object_str.replace(" ", "")
    return data_dict


def process_file_folder_rg6(folder, dataset="https://osf.io/gec6s/?view_only=979775a79d934a0083a1b2008544183e", sensor="onrobot_rg6", printable=False):
    ret = {}
    setup = {"gripper": sensor}
    ls_folder = os.listdir(folder)
    object_names = ls_folder  # its the same in this case
    object_contexts = {}
    measurement_templates = {}  # template per folder
    for on in object_names:
        measurement_template = {}
        measurement_templates[on] = measurement_template
        measurement_template["object_context"] = {}
        object_context = measurement_template["object_context"]
        common_names = {"kinovacube": "white_kinova_cube_light"}  # FIXME: THIS USES ALREADY EXISTING NAMES => check the database
        object_context["common_name"] = on if common_names.get(on) is None else common_names.get(on)
        object_context["dataset_id"] = on
        object_context["dataset"] = dataset
        object_context["other"] = {}
        # TODO: measurement parameters in the database, e.g. gripper closing speed absolute, gripper closing speed relative
        # print(object_context)

        on_folder = os.path.join(folder, on)
        ls_measurement_folder = os.listdir(on_folder)
        for measurement_file in ls_measurement_folder:
            abs_file_path = os.path.join(on_folder, measurement_file)
            measurement_dict = {}
            measurement_dict["object_instance"] = object_context
            data_dict = process_rg6_type(abs_file_path, printable=printable)
            measurement_dict["sensor_outputs"] = {}
            sensor_output_dict = measurement_dict["sensor_outputs"]
            sensor_output_dict[sensor] = data_dict
            parameter_value = re.search("[^-]+[.]txt$", measurement_file).group().replace(".txt", "")
            object_context["other"]["object_size"] = parameter_value + "mm"  # FIXME: THIS IS SPECIFIC FOR RG6

            # setup
            measurement_dict["setup"] = setup
            ret[abs_file_path] = {"measurement": measurement_dict}
            # print(measurement_dict)
    return ret


def process_file_folder_2f85(folder, dataset="https://osf.io/gec6s/?view_only=979775a79d934a0083a1b2008544183e", sensor="robotiq_2f85", measurement_parameters=None, printable=False):
    setup = {"gripper": sensor}
    ls_folder = os.listdir(folder)
    object_names = ls_folder  # its the same in this case
    object_contexts = {}
    measurement_templates = {}  # template per folder
    ret = {}
    for on in object_names:
        measurement_template = {}
        measurement_templates[on] = measurement_template
        measurement_template["object_context"] = {}
        object_context = measurement_template["object_context"]
        common_names = {"kinovacube": "white_kinova_cube_light"}  # FIXME: THIS USES ALREADY EXISTING NAMES => check the database
        object_context["common_name"] = on if common_names.get(on) is None else common_names.get(on)
        object_context["dataset_id"] = on
        object_context["dataset"] = dataset
        object_context["other"] = {}
        # TODO: measurement parameters in the database, e.g. gripper closing speed absolute, gripper closing speed relative
        # print(object_context)

        on_folder = os.path.join(folder, on)
        ls_measurement_folder = os.listdir(on_folder)
        for measurement_file in ls_measurement_folder:
            abs_file_path = os.path.join(on_folder, measurement_file)
            measurement_dict = {}
            measurement_dict["object_instance"] = object_context
            data_dict = process_rg6_type(abs_file_path, has_object_line=False, selected_data_columns=[0,1,2], printable=printable)
            measurement_dict["sensor_outputs"] = {}
            sensor_output_dict = measurement_dict["sensor_outputs"]
            data_dict["parameters"] = measurement_parameters
            sensor_output_dict[sensor] = data_dict
            parameter_value = measurement_file.split("-")[-2]
            object_context["other"]["object_size"] = parameter_value + "mm"  # FIXME: THIS IS SPECIFIC FOR RG6
            # print(measurement_dict)

            # setup
            measurement_dict["setup"] = setup
            ret[abs_file_path] = {"measurement": measurement_dict}
    return ret


def folder_name_to_parameters_rg6(folder_name: str):
    under_split = folder_name.split("_")
    # print("re.search(\"^[^_]+\", folder_name).group()", re.search("^[^_]+", folder_name).group())
    replace_last__ = lambda x: re.sub("_+$", "", x)
    param_units = [replace_last__(x.group()[1:]) for x in re.finditer(r"[\d][a-zA-Z_]+", folder_name)]
    param_values = [x.group() for x in re.finditer(r"[+-]?([0-9]*[.])?[0-9]+", folder_name)]
    param_name = replace_last__(re.search("[a-zA-Z]+_", folder_name).group())
    # print(param_name)
    # print(list(zip(param_values, param_units)))
    ret = {}
    # clos
    for v,u in zip(param_values, param_units):
        ret[param_name+"_"+u.replace("_", "/")] = v
    # print(ret)
    # print(re.search(r"[+-]?([0-9]*[.])?[0-9]+", folder_name).group())
    return ret


def process_parameter_folder_2f85(top_folder, dataset="https://osf.io/gec6s/?view_only=979775a79d934a0083a1b2008544183e", sensor="robotiq_2f85", measurement_parameters=None, printable=False):
    ls_folder = os.listdir(top_folder)  # folders with the parameters in the name
    parameter_folders = ls_folder  # its the same in this case
    ret = {}
    for parameter_folder in parameter_folders:
        measurement_parameters = folder_name_to_parameters_rg6(parameter_folder)
        processed_measurements = process_file_folder_2f85(os.path.join(top_folder, parameter_folder), measurement_parameters=measurement_parameters, printable=printable)
        for p in processed_measurements:
            ret[p] = processed_measurements[p]
        # print(parameter_folder, measurement_parameters)
    return ret


if __name__ == "__main__":
    process_file = "C:/Users/jhart/PycharmProjects/butler/butler/dataset/Squeezing/squeezing_data/Onrobot_RG6/Mixed-set/RP1725/RG6-2020-10-02-16-22-RP1725-41.txt"
    # process_rg6_type(process_file)
    printable = False
    onrobot_rg6_measurements = process_file_folder_rg6("C:/Users/jhart/PycharmProjects/butler/butler/dataset/Squeezing/squeezing_data/Onrobot_RG6/Mixed-set", printable=printable)
    robotiq_2f85_measurements = process_parameter_folder_2f85("C:/Users/jhart/PycharmProjects/butler/butler/dataset/Squeezing/squeezing_data/Robotiq_2F-85/Mixed-set", printable=printable)
    for r in onrobot_rg6_measurements:
        print("upload_dict_"+os.path.basename(r))
    for r in robotiq_2f85_measurements:
        print("upload_dict_"+os.path.basename(r))

    # print(type(onrobot_rg6_measurements))
    # print(type(robotiq_2f85_measurements))
    abs_names = {**onrobot_rg6_measurements, **robotiq_2f85_measurements}  # only high version of python
    assert printable == False, "json dumping will fail on np.ndarray by default, set `printable=False`"
    for r in abs_names:
        # 1. take only the file name from the absolute path
        # 2. replace the extension with .json
        # 3. prepend "upload_dict_"
        # 4. put it in the config.upload_dicts_directory
        upload_dict_name = os.path.join(config.upload_dicts_directory, "upload_dict_"+os.path.splitext(os.path.basename(r))[0]+".json")
        with open(upload_dict_name, "w") as f:
            json.dump(obj=abs_names[r], fp=f)
    # print(abs_names)
    # print(onrobot_rg6_measurements)
    # print(robotiq_2f85_measurements)
