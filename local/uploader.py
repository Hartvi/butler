from __future__ import print_function, division

import requests
import json

import norach


def post_measurement(auth_tuple,
                     endpoint="http://127.0.0.1:8000/rest/",
                     data=None,
                     file_paths=None,
                     ):
    """This posts a measurement to http://localhost:8000/rest/measurements/

    Parameters
    ----------
    auth_tuple : tuple[str] or list[str]
        The (user, pass) authentication tuple.
    endpoint : str
        Basically the website name. Default is the localhost.
    data : dict[str, str]
        The dict in the format `str: json_str` {"measurement": "{"measurement": ..., "entry": ...}"}
    file_paths : dict[str, str or unicode]
        Dictionary containing the file paths to be uploaded to the server.
        Format: {server destination: abs_path}. E.g. {"measurement png": /tmp/img.png}
    """

    path = "measurements/"
    method = "POST"
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
    with open(r"/tests/testy_json.json", "r") as fp:
        stewarded_dict = json.load(fp)
        upload_dict = {"measurement": json.dumps(stewarded_dict)}
        file_paths = norach.get_file_names(stewarded_dict)
        print("file_paths:", file_paths)

        print(
        post_measurement(auth_tuple=("jeff", "jeff"),
                         endpoint="http://127.0.0.1:8000/rest/",
                         data=upload_dict,
                         file_paths=file_paths)
        )
        # print("file names:", norach.get_file_names(stewarded_dict))
