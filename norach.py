import json
import os
import requests
from PIL import Image

ENDPOINT = "http://127.0.0.1:8000/rest/"

# IMG = r'C:/Users/jhart/PycharmProjects/ipalm-database/utilities/banana.png'
# IMG = 'C:/Users/jhart/PycharmProjects/ipalm-database/utilities/banana300.png'


def send_request(method="GET", path="/", data=None, data_files=None):
    if data is None:
        data = {}
    if img_path is not None:
        with open(img_path, 'rb') as image:
            img_file = {"png": image}
            # data['file'] = image
            req = requests.request(method, ENDPOINT + path, auth=('jeff','jeff'), data=data, files=img_file)
    else:
        req = requests.request(method, ENDPOINT + path, data=data)
    return req.text


def get_measurement_image_path(experiment_dir):


def post_measurement(auth_tuple=("user", "pass"), data=None, img_path=None):
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


with open('testy_json.json', 'r') as fp:
    measurement_dict = json.load(fp)
    measurement_json = json.dumps(measurement_dict)
    measurement_data = {"measurement": measurement_json}
    img_path = "C:/Users/jhart/PycharmProjects/ipalm-database/tests/banana300.png"

    print("post_data:", measurement_dict)
    res = send_request(method="POST", path="measurements/", data=measurement_data, img_path=img_path)


print(res)
