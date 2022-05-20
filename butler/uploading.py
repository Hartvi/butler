from __future__ import print_function, division

import requests
import json
import os

import utils, config


def get_file_names(formatted_dict):
    """Collects the file names to be uploaded to the server from the formatted dictionary.

    Parameters
    ----------
    formatted_dict : dict
        The dictionary as it is output by `formatting.experiment_to_json`

    Returns
    -------
    dict
        A dictionary with:
            `keys`: Space-notation strings to where the files belong on the server. E.g. measurement.png / measurement["png"] => "measurement png".\n
            `values`: Absolute file paths on the local machine.
    """
    ret = dict()
    # sensor files:
    measurement = formatted_dict["measurement"]
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

    entry = formatted_dict["entry"]
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
    """This posts a measurement to http://endpoint/measurements/

    Parameters
    ----------
    auth_tuple : tuple[str] or list[str]
        The (user, pass) authentication tuple.
    uploaded_dicts_statuses : str
        Upload statuses of the dictionaries: true/false.
    endpoint : str
        Basically the website name. Default is the localhost.
    dict_path : str
        Path to the formatted dictionary.
    """
    dict_path = dict_path.replace("\\", "/")
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
    print("data: ", data)
    print("file_paths: ", file_paths)
    # with open(dict_path, 'r') as fp:
    #     upload_status = False
    #     if upload_duplicates:
    #         upload_status = uploaded_dicts_statuses
    if file_paths is not None:
        req = requests.request(method, endpoint + path, auth=auth_tuple, data=data, files=file_bytes)
    else:
        req = requests.request(method, endpoint + path, data=data)
    for file_designation in file_bytes:
        file_bytes[file_designation].close()
    try:
        json.loads(req.text)
        utils.update_json(p=config.uploaded_dicts_json, update_dict={dict_path: True})
        return True
    except json.JSONDecodeError as e:
        utils.update_json(p=config.uploaded_dicts_json, update_dict={dict_path: False})
        return False
    # return req.text


def post_measurements(auth_tuple, endpoint, dict_paths, upload_statuses=config.uploaded_dicts_json, upload_duplicates=False):
    """Posts posts measurements located in `dict_paths` and updates the `config.uploaded_dicts_json` file.

    Parameters
    ----------
    auth_tuple : tuple[str] or list[str]
        The (user, pass) authentication tuple.
    endpoint : str
        Basically the website name. Default is the localhost.
    dict_paths : list[str]
        Paths to the formatted dictionaries.
    upload_duplicates : bool
        Whether to upload a name that has been flagged as `true` in `config.uploaded_dicts_json`
    upload_statuses : str
        Path to the dictionary with the upload statuses of the paths `dict_paths`.
        E.g. "/home/meas_2022_02_02_property.json": true => already uploaded, don't upload

    """
    succeeded_status = dict()

    with open(upload_statuses, "r") as fp:
        upload_statuses_dict = json.load(fp)

    for dict_path in dict_paths:
        dp = dict_path.replace("\\", "/")
        dict_status = upload_statuses_dict.get(dp)  # None or False if not uploaded yet
        # print(dp, not upload_duplicates, dict_status)
        if not upload_duplicates and dict_status:
            continue
        succ = post_measurement(auth_tuple=auth_tuple,
                                endpoint=endpoint,
                                dict_path=dp)
        succeeded_status[dp] = succ
    # if verbose:
    #     print(json.dumps(succeeded_status))
    return succeeded_status


def list_upload_paths(parent_dir=config.upload_dicts_directory):
    parent_ls = os.listdir(parent_dir)
    ret = list(map(lambda x: os.path.join(parent_dir, x), parent_ls))
    return ret


def lazy_post_measurements(auth_tuple, endpoint):
    dict_paths = list_upload_paths()
    # print(len(dict_paths))
    ret = post_measurements(auth_tuple, endpoint, dict_paths)
    return ret


if __name__ == "__main__":
    """
    print("\nuploader: butler:")
    os.system("python C:/Users/jhart/PycharmProjects/butler/butler.py")
    print("\nuploader: :")
    os.system("python C:/Users/jhart/PycharmProjects/butler/formatting.py")
    print("\nuploader: :")
    os.system("python C:/Users/jhart/PycharmProjects/butler/uploading.py")
    """

    # dict_path = r"C:/Users/jhart/PycharmProjects/butler/butler/upload_dicts/upload_dict_2022_04_29_16_51_04_cat-vision_1.json"
    res = lazy_post_measurements(auth_tuple=("jeff", "jeff"),
                                 endpoint="http://127.0.0.1:8000/rest/")
    print("result:\n", json.dumps(res))
    # print(
    #     post_measurement(auth_tuple=("jeff", "jeff"),
    #                      endpoint="http://127.0.0.1:8000/rest/",
    #                      dict_path=dict_path)
    # )
