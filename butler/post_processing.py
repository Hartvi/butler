import json
import os

import utils


def change_experiment_jsons(update_dict, experiment_directory, json_file_name, rule):
    wlk = list(os.walk(experiment_directory))  # a, b, c; a=dir, b=subdirs, c=files
    for a, b, c in wlk:
        if rule(a):
            p = os.path.join(a, json_file_name)
            try:
                utils.update_json(p, update_dict)
                print("rule passed: ", p)
            except:
                pass


if __name__ == '__main__':
    pass
    # example how to add the "repository" field to a measurement JSON. This will appear in the entry
    change_experiment_jsons({"repository": "https://github.com/hartvjir/detectron2"},
                 "C:/Users/jhart/PycharmProjects/butler/butler/experiments/experiment_2022_04_29_17_06_08",
                 "measurement.json",
                            lambda x: "at-vision" in x)

