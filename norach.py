from __future__ import print_function, division
import json
import os
import requests
from PIL import Image

ENDPOINT = "http://127.0.0.1:8000/rest/"

# IMG = r'C:/Users/jhart/PycharmProjects/ipalm-database/utilities/banana.png'
# IMG = 'C:/Users/jhart/PycharmProjects/ipalm-database/utilities/banana300.png'


def get_measurement_image_path(experiment_dir):
    ls_exp = os.listdir(experiment_dir)
    img_file = filter(lambda x: x == "img.png", ls_exp)
    if not img_file:
        img_file = filter(lambda x: ".png" in x, ls_exp)
    if not img_file:
        return None
    img_file = img_file[0]
    return img_file


def to_absolute(some_path, parent_dir):
    existing_path = None
    possible_path = os.path.join(parent_dir, some_path)
    if not os.path.isfile(possible_path):
        raise ValueError("File " + str(possible_path) + " doesn't exist!")
    else:
        existing_path = possible_path
    if not os.path.isfile(some_path):
        raise ValueError("File " + str(some_path) + " doesn't exist!")
    else:
        existing_path = some_path
    return existing_path


def get_property_data_file_paths(property_dir):  # measurement.json => ["other_file"]
    with open(os.path.join(property_dir, "data", "measurement.json"), "r") as fp:
        measurement_dict = json.load(fp)

    other_file = measurement_dict.get("other_file")
    if not other_file:
        return None
    ret = dict()
    if type(other_file) in {list, tuple}:
        for i in range(len(other_file)):
            ret["other_file_"+str(i)] = to_absolute(property_dir, other_file[i])
    elif type(other_file) == str:
        ret["other_file"] = to_absolute(property_dir, other_file)
    elif type(other_file) == dict:
        for k in other_file:
            other_file[k] = to_absolute(property_dir, other_file)
    return other_file


def get_property_folder_list(experiment_dir):
    ls_exp = os.listdir(experiment_dir)
    ret = [os.path.join(experiment_dir, _) for _ in ls_exp if os.path.isdir(os.path.join(experiment_dir, _))]
    return ret


def post_measurement(experiment_folder, auth_tuple=("user", "pass"), data=None, img_path=None):
    path = "measurements/"
    method = "POST"
    if img_path is not None:
        with open(img_path, 'rb') as image:
            img_file = {"png": image}
            # data['file'] = image
            req = requests.request(method, ENDPOINT + path, auth=('jeff','jeff'), data=data, files=img_file)
    else:
        req = requests.request(method, ENDPOINT + path, data=data)
    return req.text


def get_file_names(stewarded_dict):
    """
    todo files:
    - sensor_outputs
    - object_instance
    - property_elements
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


if __name__ == "__main__":
    exp_folder = r"C:\Users\jhart\PycharmProjects\butler\experiment_0"
    # print(get_measurement_image_path(exp_folder))
    # print(get_property_folder_list(exp_folder))
    # for prop_folder in get_property_folder_list(exp_folder):
    #     print(get_property_data_file_paths(prop_folder))
    with open(r"C:\Users\jhart\PycharmProjects\butler\tests\testy_json.json", "r") as fp:
        stewarded_dict = json.load(fp)
        print("file names:", get_file_names(stewarded_dict))
    pass
