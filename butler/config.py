import os

# for butler.py
# change to fit your needs
experiment_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), "experiments")
"""The path to the directory containing the experiments."""
if not os.path.exists(experiment_directory):
    os.mkdir(experiment_directory)

# for formatting.py
# change to fit your needs
upload_dicts_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), "upload_dicts")
"""The path to the directory containing the formatted experiment JSONs."""
if not os.path.exists(upload_dicts_directory):
    os.mkdir(upload_dicts_directory)

uploaded_dicts_json = os.path.join(os.path.dirname(os.path.realpath(__file__)), "uploaded_dicts.json")
"""The JSON dictionary tracking the upload statuses of experiments in the experiments folder. \nWarning: Deleting this causes duplicate uploads."""
if not os.path.exists(uploaded_dicts_json):
    with open(uploaded_dicts_json, "w") as fp:
        pass
