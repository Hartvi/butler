import json
import os

import utils

# def change_object_contexts(context_dict, experiment_directory):
#     experiment_sub_dirs = os.listdir(experiment_directory)
#     for esd in experiment_sub_dirs:
#         try:
#             int(esd.split('_')[-1])
#             object_context_path = os.path.join(experiment_directory, esd, 'data', 'object_context.json')
#             update_json(object_context_path, context_dict)
#         except:
#             pass


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

