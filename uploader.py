from __future__ import print_function, division

import os
import requests
import json

import butler2, norach, steward


def post_measurement(auth_tuple,
                     endpoint="http://127.0.0.1:8000/rest/",
                     path="measurements/",
                     data=None,
                     file_paths=None,
                     method="POST",
                     ):

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
    print("\nuploader: butler2:")
    os.system("python C:/Users/jhart/PycharmProjects/butler/butler2.py")
    print("\nuploader: steward:")
    os.system("python C:/Users/jhart/PycharmProjects/butler/steward.py")
    print("\nuploader: norach:")
    os.system("python C:/Users/jhart/PycharmProjects/butler/norach.py")
    """

    print("\nuploader: uploader")
    with open(r"C:\Users\jhart\PycharmProjects\butler\tests\testy_json.json", "r") as fp:
        stewarded_dict = json.load(fp)
        upload_dict = {"measurement": json.dumps(stewarded_dict)}
        file_paths = norach.get_file_names(stewarded_dict)

        print(
        post_measurement(auth_tuple=("jeff", "jeff"),
                         endpoint="http://127.0.0.1:8000/rest/",
                         path="measurements/",
                         data=upload_dict,
                         file_paths=file_paths)
        )
        # print("file names:", norach.get_file_names(stewarded_dict))
