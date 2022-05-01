import os

# butler.py
# change to fit your needs
experiment_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), "experiments")
if not os.path.exists(experiment_directory):
    os.mkdir(experiment_directory)

# formatting.py
# change to fit your needs
upload_dicts_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), "upload_dicts")
if not os.path.exists(upload_dicts_directory):
    os.mkdir(upload_dicts_directory)

uploaded_dicts_json = os.path.join(os.path.dirname(os.path.realpath(__file__)), "uploaded_dicts.json")
if not os.path.exists(uploaded_dicts_json):
    with open(uploaded_dicts_json, "w") as fp:
        pass
