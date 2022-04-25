from __future__ import print_function, division
import json
import os
import requests
from PIL import Image

ENDPOINT = "http://127.0.0.1:8000/rest/"

# IMG = r'C:/Users/jhart/PycharmProjects/ipalm-database/utilities/banana.png'
# IMG = 'C:/Users/jhart/PycharmProjects/ipalm-database/utilities/banana300.png'


def _get_measurement_image_path(experiment_dir):
    ls_exp = os.listdir(experiment_dir)
    img_file = filter(lambda x: x == "img.png", ls_exp)
    if not img_file:
        img_file = filter(lambda x: ".png" in x, ls_exp)
    if not img_file:
        return None
    img_file = img_file[0]
    return img_file


def _to_absolute(some_path, parent_dir):
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


def _get_property_data_file_paths(property_dir):  # measurement.json => ["other_file"]
    with open(os.path.join(property_dir, "data", "measurement.json"), "r") as fp:
        measurement_dict = json.load(fp)

    other_file = measurement_dict.get("other_file")
    if not other_file:
        return None
    ret = dict()
    if type(other_file) in {list, tuple}:
        for i in range(len(other_file)):
            ret["other_file_"+str(i)] = _to_absolute(property_dir, other_file[i])
    elif type(other_file) == str:
        ret["other_file"] = _to_absolute(property_dir, other_file)
    elif type(other_file) == dict:
        for k in other_file:
            other_file[k] = _to_absolute(property_dir, other_file)
    return other_file


def _get_property_folder_list(experiment_dir):
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


if __name__ == "__main__":
    exp_folder = r"C:\Users\jhart\PycharmProjects\butler\experiment_2022_04_23_18_27_13"
    # print(_get_measurement_image_path(exp_folder))
    # print(_get_property_folder_list(exp_folder))
    # for prop_folder in _get_property_folder_list(exp_folder):
    #     print(_get_property_data_file_paths(prop_folder))
    with open(r"/tests/tesy_json.json", "r") as fp:
        stewarded_dict = json.load(fp)
        print("file names:", get_file_names(stewarded_dict))
    pass
