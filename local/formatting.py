from __future__ import print_function, division
import os
import json
import re

from os.path import join

from local import conf
from utils import file_dirs


_experiment_ignored_names = r"(.*\..*)|(timestamp.*)"  # |(?!(.*\.json))
_property_ignored_names = r"(log.txt)|(figs)|(imgs)"


def _data_dicts_to_sensor_outputs(sensor_outputs, data_dict, setup_dict, prop_dir):
    # ret = dict()
    # if type(data_dict) != list and type(data_dict) == dict:
    #     data_dict = [data_dict, ]
    # elif type(data_dict) != list:
    #     raise TypeError("data_dict isn't a Union[dict, list]: " + str(data_dict))
    # print(sensor_outputs)
    # print("data_dict", data_dict)
    for sn in data_dict:  # sn = sensor name
        # if the user entered the sensor name: ok; else if the type of sensor: convert to sensor name
        # e.g. `gripper: robotiq 2f85` : it ends up being "robotiq 2f85" even if the user enters "gripper" as the source
        if sn in setup_dict:
            data_source = setup_dict[sn]
        elif sn in setup_dict.values():
            data_source = sn
        else:
            raise KeyError("data source/sensor `"+str(sn)+"` not specified in experiment_i/setup.json: "+str(setup_dict))

        data_values = data_dict[sn]
        print("data_values: ", data_values)
        print("sensor_outputs.keys()", sensor_outputs.keys())
        data_source_exists = data_source in sensor_outputs  # if a sensor has already been added to `sensor_outputs`
        sensor_output_keys = sensor_outputs[data_source].keys() if data_source_exists else list()
        data_dict_keys = data_values.keys()  # the new arrivals - the keys that are about to be added

        # if a modality has already been added and one tries to add it again
        # e.g. sensor_outputs: already exists; data_dict: not existing, want to add this to sensor_outputs
        #   sensor_outputs = {"2f85" : {"time": [0.01, 0.02]}} AND data_dict = {"2f85": {"time": [3, 4, 5]}}
        #   it's ambiguous to add the modality `time` from `data_dict` to an already existing `time` in `sensor_outputs`
        if len(set(sensor_output_keys) & set(data_dict_keys)) != 0:
            raise KeyError("source \"" + str(data_source) + "\" has colliding modalities: " +
                           str(sensor_output_keys) + " VS " + str(data_dict_keys))
        # if sensor is registered, just append the values
        if data_source_exists:
            for modality in data_values:
                # print("sensor_outputs[data_source][modality]", sensor_outputs[data_source][modality])
                sensor_outputs[data_source][modality] = data_values[modality]
        else:
            sensor_outputs[data_source] = data_values
        outs = sensor_outputs[data_source]
        for modality in outs:
            for fd in file_dirs:
                output_name = str(outs[modality])
                p = join(prop_dir, fd, output_name)
                if os.path.isfile(p) and p != output_name:
                    # print("path before: ", output_name)
                    outs[modality] = p
                    # print("path after: ", p)
        # print("sensor_outputs[data_source]: ", sensor_outputs[data_source])


def _make_one_entry(parameters, entry_value, measurement_object_json):
    entry_value["std"] = parameters["std"]
    entry_value["mean"] = parameters["mean"]
    units = None
    meas_units = measurement_object_json["units"]
    if meas_units:
        units = meas_units
    elif "units" in parameters:
        units = parameters["units"]
    entry_value["units"] = units
    property_name = None
    meas_property_name = measurement_object_json["property_name"]
    if meas_property_name:
        property_name = meas_property_name
    elif "property_name" in parameters:
        property_name = parameters["property_name"]
    entry_value["name"] = property_name


def experiment_to_json(experiment_directory, out_file=None):
    """Takes a butlered experiment folder and converts it into a dictionary that is in the format that will be uploaded to the server.

    Parameters
    ----------
    experiment_directory : str
        The experiment{i} directory containing the directory structure as specified in butler.py
    out_file : str or None
        Absolute path to the output file. "*.json" to write to the output file, None to not write to a file.

    Returns
    -------
    dict
        Returns the processed experiment in the form of a dict, which close to the final format for uploading.
    """
    if out_file is None:
        out_file = "upload_dict_"+"_".join(experiment_directory.split("_")[-6:]) + ".json"
        out_file = os.path.abspath(os.path.join(conf.upload_dicts_directory, out_file))
    prop_dirs = os.listdir(experiment_directory)
    valid_dirs = list()
    for _ in prop_dirs:
        matches = re.findall(pattern=_experiment_ignored_names, string=_)
        if len(matches) == 0:
            valid_dirs.append(_)
    setup_file = join(experiment_directory, "setup.json")
    with open(setup_file, "r") as fp:
        setup_dict = json.load(fp)  # final, 1 for N objects
    valid_prop_dirs = list()
    for prop_dir in valid_dirs:
        abs_prop_dir = join(experiment_directory, prop_dir)
        valid_prop_dirs.append(abs_prop_dir)
        # print(abs_prop_dir)
        # sub_prop_dirs = os.listdir(abs_prop_dir)
        # for _ in sub_prop_dirs:
        #     matches = re.findall(pattern=_property_ignored_names, string=_)
        #     if len(matches) == 0:
        #         valid_prop_dirs.append(join(abs_prop_dir, _))
    # print(valid_prop_dirs)

    # prop_name = prop_dir.split("_")[0]
    # print(prop_name)
    object_context_dict = None
    # print("valid_prop_dirs", valid_prop_dirs)
    for prop_dir in valid_prop_dirs:
        data_dir = join(prop_dir, "data")
        certain_files = {"object_context": "object_context.json", "measurement": "measurement.json"}
        object_context_file = join(data_dir, certain_files["object_context"])
        if os.path.exists(object_context_file):
            with open(object_context_file, "r") as fp:
                object_context_dict = json.load(fp)  # max N for N objects
            # print(data_dir, ":", object_context_json)
        # SensorOutputs, PropertyEntry, Grasp
        measurement_object_file = join(data_dir, certain_files["measurement"])
        with open(measurement_object_file, "r") as fp:
            measurement_object_dict = json.load(fp)
        # print("measurement_object_dict", measurement_object_dict)
        data_dir_ls = os.listdir(data_dir)
        data_jsons = [_ for _ in data_dir_ls if (_ not in certain_files.values() and ".json" in _)]

        sensor_outputs = dict()
        meas_values = measurement_object_dict["values"]

        # print("experiment_directory: ", experiment_directory, "data_dir", prop_dir)
        if meas_values is not None:  # if `meas_object.values` is filled
            _data_dicts_to_sensor_outputs(sensor_outputs, meas_values, setup_dict, prop_dir)
        for data_json in data_jsons:  # if `data_variables` is filled
            # print("data json: ", join(data_dir, data_json))
            with open(join(data_dir, data_json), "r") as fp:
                data_dict = json.load(fp)
                _data_dicts_to_sensor_outputs(sensor_outputs, data_dict, setup_dict, prop_dir)
        print("setup_json:", setup_dict)
        print("object_context:", object_context_dict)
        print("sensor_outputs:", sensor_outputs)
        # print("_measurement_object:", measurement_object_dict)
        entry_dict = dict()
        entry_dict["values"] = list()
        entry_values = entry_dict["values"]
        measurement_type = measurement_object_dict["measurement_type"]  # ["continuous", "categorical"]
        parameters = measurement_object_dict["parameters"]  # {"cat1": 0.1, "cat2": 0.5, "cat3": 0.4}
        entry_dict["type"] = measurement_object_dict["measurement_type"]
        entry_dict["name"] = measurement_object_dict["property_name"]
        entry_dict["repository"] = measurement_object_dict["repository"]
        # care about prop.units, params[std, mean], prop_name
        if measurement_type == "continuous":
            # if measurement 1D {std, mean}, then just a single continuous distribution
            if len(set(parameters) & {"std", "mean"}) == 2:  # 1D
                entry_value = dict()
                entry_values.append(entry_value)
                _make_one_entry(parameters, entry_value, measurement_object_dict)  # inplace change entry_value dict
            else:
                for prop_k in parameters:
                    prop_v = parameters[prop_k]
                    if type(prop_v) != dict:
                        continue
                    entry_value = dict()
                    entry_values.append(entry_value)
                    _make_one_entry(parameters, entry_value, measurement_object_dict)
        elif measurement_type == "categorical":
            cat_sum = sum(parameters.values())
            if abs(cat_sum - 1.0) > 0.01:
                raise ValueError("Sum of categories' probabilities must be equal to one! Current sum: "+str(cat_sum))
            # normalize as closely to one as possible
            parameters = {cat: parameters[cat] / cat_sum for cat in parameters}
            for cat in parameters:
                prop_el = {"name": cat, "probability": parameters[cat]}
                entry_values.append(prop_el)
            if entry_dict["name"] in {"stiffness", "elasticity", "size"}:
                raise KeyError(str(entry_dict["name"])+" is not a categorical property")

        grasp = measurement_object_dict.get("grasp")
        if grasp is not None:
            assert len({"rotation", "position", "grasped"} & set(grasp.keys())) == 3, \
                "`grasp` dictionary must contain keys \"position\": xyz, \"rotation\": xyz, \"grasped\": bool"
        print("grasp", grasp)
        object_pose = measurement_object_dict.get("object_pose")
        if object_pose is not None:
            assert len({"rotation", "position"} & set(object_pose.keys())) == 2, \
                "`object_pose` dictionary must contain keys \"position\": xyz, \"rotation\": xyz"
        print("object_pose", object_pose)

        print("data_dir:", prop_dir)
        potential_img_dir = join(data_dir, "img.png")

        print("entry_object", entry_dict)

        request_dict = dict()
        request_dict["measurement"] = dict()
        measurement_dict = request_dict["measurement"]
        measurement_dict["object_instance"] = object_context_dict

        if os.path.exists(potential_img_dir):
            print("img.png:", potential_img_dir)
            measurement_dict["png"] = potential_img_dir
        # else:
        #     print("IMAGE PNG DOESNT EXIST")
        measurement_dict["setup"] = setup_dict
        measurement_dict["sensor_outputs"] = sensor_outputs
        measurement_dict["grasp"] = grasp
        measurement_dict["object_pose"] = object_pose
        request_dict["entry"] = entry_dict
        # print("\nrequest_dict: ", request_dict, "\n")
        with open(out_file, "w") as fp:
            json.dump(fp=fp, obj=request_dict, indent=True)
        return request_dict
