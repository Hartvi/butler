from __future__ import print_function, division

import requests
import json
import os

import utils


def get_file_names(stewarded_dict):
    """Collects the file names to be uploaded to the server from the "stewarded" dictionary.

    Parameters
    ----------
    stewarded_dict : dict
        The dictionary as is output by `~steward.experiment_to_json`

    Returns
    -------
    dict
        A dictionary with:
            `keys`: Space-notation strings to where the files belong on the server. E.g. measurement.png / measurement["png"] => "measurement png".\n
            `values`: Absolute file paths on the local machine.
    """
    ret = dict()
    # sensor files:
    measurement = stewarded_dict["measurement"]
    sensor_outputs = measurement["sensor_outputs"]
    png = measurement.get("png")
    if png is not None:
        if os.path.isfile(str(png)):
            ret["measurement png"] = png
        else:
            raise ValueError("png: `" + str(png) + "` is not a file!!")
    # else:
    #     print("\033[1;33mRecommended `exp../{prop}/data/img.png` not present in request[\"measurement\"] dictionary\033[0m")

    for sensor_name in sensor_outputs:
        # print("sensor_name", sensor_name)
        output_quantities = sensor_outputs[sensor_name]
        for output_quantity in output_quantities:
            # print("output_quantity", output_quantity)
            single_output = output_quantities[output_quantity]
            # print("single_output", single_output)
            # print("type:", type(single_output))
            single_output_str = str(single_output)

            if os.path.isfile(single_output_str):
                ret["measurement "+str(sensor_name)+" "+str(output_quantity)] = single_output
            elif os.path.isabs(single_output_str):
                raise IOError("An absolute path is provided, but doesn't point to an actual file!!! `"+single_output_str+"`")

            # if type(single_output) == str:
            #     if os.path.isfile(single_output):
            #         ret["measurement "+str(sensor_name)+" "+str(output_quantity)] = single_output
            # else:
            #     raise ValueError("`"+str(single_output)+"` is not a file!!")
    object_instance_str = "object_instance"
    object_instance = measurement[object_instance_str]
    object_instance_file = object_instance.get("other_file")
    if object_instance_file is not None:
        if os.path.isfile(str(object_instance_file)):
            ret["measurement "+object_instance_str] = object_instance_file
        else:
            raise ValueError("object_instance.other_file: `" + str(object_instance_file) + "` is not a file!!")

    entry = stewarded_dict["entry"]
    values = entry["values"]
    for v in values:
        value_file = v.get("other_file")
        if value_file is not None:
            if os.path.isfile(str(value_file)):
                ret["entry values " + v["name"]] = value_file
            else:
                raise ValueError("value: `" + str(value_file) + "` is not a file!!")
    return ret


def post_measurement(auth_tuple,
                     endpoint="http://127.0.0.1:8000/rest/",
                     dict_path=None,
                     ):
    """This posts a measurement to http://localhost:8000/rest/measurements/

    Parameters
    ----------
    auth_tuple : tuple[str] or list[str]
        The (user, pass) authentication tuple.
    endpoint : str
        Basically the website name. Default is the localhost.
    dict_path : str
        The dict in the format `str: json_str` {"measurement": "{"measurement": ..., "entry": ...}"}
    """

    path = "measurements/"
    method = "POST"
    # collect dict
    with open(dict_path, "r") as fp:
        upload_dict = json.load(fp)
        data = {"measurement": json.dumps(upload_dict)}

    # collect files to be uploaded
    file_paths = get_file_names(upload_dict)

    file_bytes = dict()
    for file_designation in file_paths:
        f = open(file_paths[file_designation], 'rb')
        file_bytes[file_designation] = f
    if file_paths is not None:
        req = requests.request(method, endpoint + path, auth=auth_tuple, data=data, files=file_bytes)
    else:
        req = requests.request(method, endpoint + path, data=data)
    for file_designation in file_bytes:
        file_bytes[file_designation].close()
    return req.text


if __name__ == "__main__":
    """
    print("\nuploader: butler:")
    os.system("python C:/Users/jhart/PycharmProjects/butler/logger.py")
    print("\nuploader: steward:")
    os.system("python C:/Users/jhart/PycharmProjects/butler/steward.py")
    print("\nuploader: norach:")
    os.system("python C:/Users/jhart/PycharmProjects/butler/norach.py")
    """

    dict_path = r"../unused/tests/testy_json.json"

    print(
        post_measurement(auth_tuple=("jeff", "jeff"),
                         endpoint="http://127.0.0.1:8000/rest/",
                         dict_path=dict_path)
    )
