from __future__ import print_function
import os
import re
import json

from numpy.testing._private.parameterized import param

join = os.path.join

_experiment_ignored_names = "(log.txt)|(timestamp.*)|(setup\.json)"  # |(?!(.*\.json))
_property_ignored_names =   "(log.txt)|(figs)|(imgs)"


def merge_two_dicts(x, y):
    z = x.copy()   # start with keys and values of x
    z.update(y)    # modifies z with keys and values of y
    return z


def data_dicts_to_sensor_outputs(sensor_outputs, data_dict):
    # ret = dict()
    if type(data_dict) != list and type(data_dict) == dict:
        data_dict = [data_dict, ]
    elif type(data_dict) != list:
        raise TypeError("data_dict isn't a Union[dict, list]: " + str(data_dict))
    for output in data_dict:
        data_source = output["source"]
        data_values = output["values"]
        # {"source": "gripper_name", "values": [1,2,..] => "values": {"values": [..]}}
        if type(data_values) == list:
            tmp = data_values
            output["values"] = dict()
            output["values"]["values"] = tmp

        data_values = output["values"]
        # if data_source in sensor_outputs:
        #     raise KeyError("source \"" + str(data_source) + "\" already in sensor outputs: " + str(sensor_outputs))
        # print(output)
        # print(sensor_outputs)
        data_source_exists = data_source in sensor_outputs
        sensor_output_keys = sensor_outputs[data_source].keys() if data_source_exists else list()
        data_dict_keys = data_values.keys()
        if len(set(sensor_output_keys) & set(data_dict_keys)) != 0:
            raise KeyError("source \""+str(data_source)+"\" has colliding modalities: "+str(sensor_output_keys)+" VS "+str(data_dict_keys))
        if data_source_exists:
            for modality in data_values:
                sensor_outputs[data_source][modality] = data_values[modality]
        else:
            sensor_outputs[data_source] = data_values
        # ret[data_source] = output["values"]


def make_one_entry(parameters, entry_value, measurement_object_json):
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


# tsumari: get experiment folder, convert it to the measurement.json format then upload it
def experiment_to_json(experiment_directory):
    # type: (str) -> str
    prop_dirs = os.listdir(experiment_directory)
    valid_dirs = list()
    for _ in prop_dirs:
        matches = re.findall(pattern=_experiment_ignored_names, string=_)
        if len(matches) == 0:
            valid_dirs.append(_)
    setup_file = os.path.join(experiment_directory, "setup.json")
    with open(setup_file, "r") as fp:
        setup_dict = json.load(fp)  # final, 1 for N objects
    valid_prop_dirs = list()
    for prop_dir in valid_dirs:
        abs_prop_dir = join(experiment_directory, prop_dir)
        sub_prop_dirs = os.listdir(abs_prop_dir)
        for _ in sub_prop_dirs:
            matches = re.findall(pattern=_property_ignored_names, string=_)
            if len(matches) == 0:
                valid_prop_dirs.append(join(abs_prop_dir, _))
        # print(valid_prop_dirs)

        # prop_name = prop_dir.split("_")[0]
        # print(prop_name)
    object_context_dict = None
    print("valid_prop_dirs", valid_prop_dirs)
    for data_dir in valid_prop_dirs:
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
        print("measurement_object_dict", measurement_object_dict)
        data_dir_ls = os.listdir(data_dir)
        data_jsons = [_ for _ in data_dir_ls if _ not in certain_files.values()]

        sensor_outputs = dict()
        meas_values = measurement_object_dict["values"]
        if meas_values is not None:  # if `meas_object.values` is filled
            data_dicts_to_sensor_outputs(sensor_outputs, meas_values)
        for data_json in data_jsons:  # if `data_variables` is filled
            with open(join(data_dir, data_json), "r") as fp:
                data_dict = json.load(fp)
                data_dicts_to_sensor_outputs(sensor_outputs, data_dict)
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
                make_one_entry(parameters, entry_value, measurement_object_dict)  # inplace change entry_value dict
            else:
                for prop_k in parameters:
                    prop_v = parameters[prop_k]
                    if type(prop_v) != dict:
                        continue
                    entry_value = dict()
                    entry_values.append(entry_value)
                    make_one_entry(parameters, entry_value, measurement_object_dict)
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
                raise KeyError(entry_dict["name"]+" is not a categorical property")

        grasp = measurement_object_dict.get("grasp")
        if grasp is not None:
            assert len({"rotation", "position", "grasped"} & set(grasp.keys())) == 3, \
                "`grasp` dictionary must contain keys \"position\": xyz, \"rotation\": xyz, \"grasped\": bool"
        print("grasp", grasp)

        print("entry_object", entry_dict)

        request_dict = dict()
        request_dict["measurement"] = dict()
        measurement_dict = request_dict["measurement"]
        measurement_dict["object_instance"] = object_context_dict
        measurement_dict["setup"] = setup_dict
        measurement_dict["sensor_outputs"] = sensor_outputs
        measurement_dict["grasp"] = grasp
        request_dict["entry"] = entry_dict
        # print("\nrequest_dict: ", request_dict, "\n")
        with open("tests/testy_json.json", "w") as fp:
            json.dump(fp=fp, obj=request_dict, indent=True)


if __name__ == "__main__":
    experiment_to_json("experiment_0")


