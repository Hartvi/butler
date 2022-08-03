from __future__ import print_function, division

import copy
import os
import json
import re
from datetime import datetime as dt

from os.path import join

import config
from utils import file_dirs, get_regex, get_recursive_regex, get_experiment_dirs, date_template
import utils


_experiment_ignored_names = r"(.*\..*)|(timestamp.*)"  # |(?!(.*\.json))
_property_ignored_names = r"(log.txt)|(figs)|(imgs)"

mean_pattern = r".*(mean)|(value)|(av(era)?g(e)?).*"
std_pattern = r".*(sigma)|(std).*"
param_pattern = r".*param.*"
meas_type_pattern = r".*meas(urement)?_type.*"
meas_prop_pattern = r".*(meas(urement)?_prop)|(prop(erty)?(_name)?)|(name).*"
repo_pattern = r".*(repo(sitory)?)|(algo(rithm)?).*"  # i know it's superfluous to add the (.+)? parts
units_pattern = r".*unit.*"
value_pattern = r"(value)|(sensor)|(output).*"
pred_pattern = r".*(pred)|(out)|(est).*"


def standardize_key(d, pattern, target_key, changeflag=False):  # 1 to 1 or N to 1 depending on the regex: ()|()...
    ret = dict()
    changed = False
    for k in d:  # iterate through keys
        if len(re.findall(pattern=pattern, string=k)) > 0:
            new_val = copy.deepcopy(d[k])
            ret[target_key] = new_val
            changed = True
        else:
            ret[k] = copy.deepcopy(d[k])
    if changeflag:
        return ret, changed
    else:
        return ret


def standardize_keys_from_dict(d, patterns_dict):
    new_d = d
    for target in patterns_dict:
        new_d = standardize_key(d=new_d, pattern=patterns_dict[target], target_key=target)
    return new_d


def _data_dicts_to_sensor_outputs(sensor_outputs, data_dict, setup_dict, prop_dir):
    # print("setup_dict:", setup_dict)
    # ret = dict()
    # if type(data_dict) != list and type(data_dict) == dict:
    #     data_dict = [data_dict, ]
    # elif type(data_dict) != list:
    #     raise TypeError("data_dict isn't a Union[dict, list]: " + str(data_dict))
    # print(sensor_outputs)
    print("data_dict", data_dict)
    for sn in data_dict:  # sn = sensor name
        # if the user entered the sensor name: ok; else if the type of sensor: convert to sensor name
        # e.g. `gripper: robotiq 2f85` : it ends up being "robotiq 2f85" even if the user enters "gripper" as the source
        if sn in setup_dict:
            data_source = setup_dict[sn]
        elif sn in setup_dict.values():
            data_source = sn
        else:
            print("[warning] data source/sensor `"+str(sn)+"` not specified in experiment_i/setup.json: "+str(setup_dict))
            continue

        data_values = data_dict[sn]
        print("data_values: ", data_values)
        # exit(1)
        print("sensor_outputs.keys()", sensor_outputs.keys())
        data_source_exists = data_source in sensor_outputs  # if a sensor has already been added to `sensor_outputs`
        sensor_output_keys = sensor_outputs[data_source].keys() if data_source_exists else list()
        if data_values is None:
            print("[WARN] sensor `"+str(sn)+"` has output `None`")
            continue
        data_dict_keys = data_values.keys()  # the new arrivals - the keys that are about to be added

        # if a modality has already been added and one tries to add it again
        # e.g. sensor_outputs: already exists; data_dict: not existing, want to add this to sensor_outputs
        #   sensor_outputs = {"2f85" : {"time": [0.01, 0.02]}} AND data_dict = {"2f85": {"time": [3, 4, 5]}}
        #   it's ambiguous to add the modality `time` from `data_dict` to an already existing `time` in `sensor_outputs`
        if len(set(sensor_output_keys) & set(data_dict_keys)) != 0:
            KeyError("KeyError: source \"" + str(data_source) + "\" has colliding modalities: " +
                     str(sensor_output_keys) + " VS " + str(data_dict_keys))
            continue
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
                    outs[modality] = p.replace("\\", "/")
                    # print("path after: ", outs[modality])
        # print("sensor_outputs[data_source]: ", sensor_outputs[data_source])


def _make_one_entry(parameters, entry_value, measurement_object_json):
    std = get_regex(parameters, std_pattern, filter_out_nones=True)
    mean = get_regex(parameters, mean_pattern, filter_out_nones=True)
    entry_value["std"] = std
    entry_value["mean"] = mean
    units = None
    meas_units = get_regex(measurement_object_json, units_pattern)
    param_units = get_regex(parameters, units_pattern)
    if meas_units:
        units = meas_units
    elif param_units is not None:
        units = param_units
    entry_value["units"] = units
    property_name = None
    meas_property_name = get_regex(measurement_object_json, meas_prop_pattern, filter_out_nones=True)  # measurement_object_json["property_name"]
    param_prop_name = get_regex(parameters, meas_prop_pattern)
    print("param_prop_name", param_prop_name)
    if meas_property_name is not None:
        property_name = meas_property_name
    if param_prop_name is not None:
        property_name = param_prop_name
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

        out_file = "upload_dict_"+"_".join( os.path.basename(experiment_directory.replace("\\", "/")).replace("experiment_", "").split("_"))
        print("out_file:", out_file)
        out_file = os.path.abspath(os.path.join(config.upload_dicts_directory, out_file))
        print("out_file:", out_file)
        # exit(1)
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

    object_context_dict = None
    print("valid_prop_dirs", valid_prop_dirs)
    for prop_dir, local_prop_name in zip(valid_prop_dirs, valid_dirs):
        print("local prop dir: ", local_prop_name)
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

        meas_values = get_regex(measurement_object_dict, value_pattern)  # ["values"]

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
        measurement_type = get_regex(measurement_object_dict, meas_type_pattern)  # measurement_object_dict["measurement_type"]  # ["continuous", "categorical"]
        parameters = get_regex(measurement_object_dict, param_pattern)  # measurement_object_dict["parameters"]  # {"cat1": 0.1, "cat2": 0.5, "cat3": 0.4}
        print("parameters: ", parameters)
        entry_dict["type"] = get_regex(measurement_object_dict, meas_type_pattern)
        entry_dict["name"] = get_regex(measurement_object_dict, meas_prop_pattern)
        entry_dict["repository"] = get_regex(measurement_object_dict, repo_pattern)
        # care about prop.units, params[std, mean], prop_name
        if measurement_type == "continuous":
            # if measurement 1D {std, mean}, then just a single continuous distribution
            get_sum = 0
            for pat in [mean_pattern, std_pattern]:
                if get_regex(parameters, pat) is not None:
                    get_sum += 1

            # if len(set(parameters) & {"std", "mean"}) == 2:  # 1D
            if get_sum == 2:
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
            entry_out = parameters
            print("entry_out:", entry_out)
            try:
                # sometimes params can be a dict like so: {..., "params": {"precision": 0.7}, ...}
                cat_sum = sum(entry_out.values())
            except:
                cat_sum = -1
                pass
            print("category sum: ", cat_sum)
            if abs(cat_sum - 1.0) > 0.01:
                entry_out = get_recursive_regex(entry_out, pred_pattern)

                print("meas_values", meas_values)
                try:
                    cat_sum = sum(meas_values.values())
                except:
                    pass
                if abs(cat_sum - 1.0) > 0.01:
                    if entry_out is None:
                        entry_out = get_recursive_regex(meas_values, pred_pattern)
                    if entry_out is None:
                        raise KeyError("No name-value mapping found in entered parameters: "+str(parameters)+"\nRecursive search for keys with pattern `"+pred_pattern+"` also yielded no results.")
                else:
                    entry_out = meas_values
            cat_sum = sum(entry_out.values())
            if abs(cat_sum - 1.0) > 0.01:
                raise ValueError("Sum of categories' probabilities must be equal to one! Current sum: "+str(cat_sum))
            # normalize as closely to one as possible
            entry_out = {cat: entry_out[cat] / cat_sum for cat in entry_out}
            for cat in entry_out:
                prop_el = {"name": cat, "probability": entry_out[cat]}
                entry_values.append(prop_el)
            if entry_dict["name"] in {"stiffness", "elasticity", "size"}:
                raise KeyError(str(entry_dict["name"])+" is not a categorical property")

        grasp = measurement_object_dict.get("grasp")
        if grasp is not None:
            assert len({"rotation", "position", "translation", "grasped"} & set(grasp.keys())) == 3, \
                "`grasp` dictionary must contain keys `position/translation`: xyz, `rotation`: xyz, `grasped`: bool"
            grasp["translation"] = grasp.pop("position")
        print("grasp", grasp)

        gripper_pose = measurement_object_dict.get("gripper_pose")
        if gripper_pose is not None:
            assert len({"rotation", "position", "translation", "grasped"} & set(gripper_pose.keys())) == 3, \
                "`gripper_pose` dictionary must contain keys `position/translation`: xyz, `rotation`: xyz, `grasped`: bool"
            gripper_pose["translation"] = gripper_pose.pop("position")
        print("gripper_pose", gripper_pose)

        object_pose = measurement_object_dict.get("object_pose")
        if object_pose is not None:
            assert len({"rotation", "position", "translation"} & set(object_pose.keys())) == 2, \
                "`object_pose` dictionary must contain keys `position/translation`: xyz, `rotation`: xyz"
            object_pose["translation"] = object_pose.pop("position")
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
        measurement_dict["gripper_pose"] = gripper_pose
        request_dict["entry"] = entry_dict
        # print("\nrequest_dict: ", request_dict, "\n")
        upload_dict_path = out_file + "_" + local_prop_name + ".json"
        print("out_file:", out_file)
        print("local_prop_name:", local_prop_name)
        print("upload_dict_path:", upload_dict_path)
        with open(upload_dict_path, "w") as fp:
            json.dump(fp=fp, obj=request_dict, indent=True)
        # return request_dict


def convert_experiments(interval="__all__"):
    """Format the experiments in the `config.experiment_directory` folder to dicts.

    Parameters
    ----------
    interval : str or list
        Date interval between which to convert the experiments. \n
            Values:\n
            "__all__": all experiments - ok if you call this manually and you dont have thousands of properties\n
            [a or None, b or None] - from `a` to `b` or all before `b` or all after `a`. Format: YYYY_mm_dd_HH_MM_SS
    """
    if interval == "__all__":
        exp_dirs = get_experiment_dirs()
    else:
        assert isinstance(interval, list), "Legal values of interval are: "+'"__all__" and lists with elements in the '\
                                                                            'date format: "'+str(date_template)+'" '
        if len(interval) < 2:
            interval.append(None)
            interval.append(None)
        if interval[0] is None:
            start = dt.strptime(utils.min_date, date_template)
        else:
            start = dt.strptime(interval[0], date_template)
        if interval[1] is None:
            end = dt.strptime(utils.max_date, date_template)
        else:
            end = dt.strptime(interval[1], date_template)
        assert start < end, "Start date must be older than end date: "+str(interval[0])+" vs "+str(interval[1])
        exp_dirs = get_experiment_dirs(extra_rule=utils.compare_interval("experiment_", start, end))
    for exp_dir in exp_dirs:
        experiment_to_json(exp_dir)

    return exp_dirs



