import json
import os

import utils


def change_experiment_jsons(update_dict, experiment_directory, json_file_name, rule, replace=False):
    wlk = list(os.walk(experiment_directory))  # a, b, c; a=dir, b=subdirs, c=files
    for a, b, c in wlk:
        if rule(a):
            p = os.path.join(a, json_file_name)
            try:
                if replace:
                    utils.replace_json(p, update_dict)
                else:
                    utils.update_json(p, update_dict)
                print("rule passed: ", p)
            except:
                pass


if __name__ == '__main__':
    pass
    # example how to add the "repository" field to a measurement JSON. This will appear in the entry
    directory_to_change = "C:/Users/jhart/PycharmProjects/butler/butler/experiments/experiment_2022_05_03_15_54_05"
    # I forgot to change the object context before the measurement:
    # change_experiment_jsons({"dataset_id": "025_mug", "common_name": "enamel_mug_ycb"},
    #                         directory_to_change,
    #                         "object_context.json",
    #                         lambda x: True)

    # I forgot to shit the z up by 5:
    # directory_to_change = "C:/Users/jhart/PycharmProjects/butler/butler/experiments/experiment_2022_04_29_16_51_04"
    # change_experiment_jsons({"object_pose": {"position": [0.465, -0.013, 0.081], "rotation": [173.309, 15.525, -21.009]}},
    #                         directory_to_change,
    #                         "measurement.json",
    #                         lambda x: True)

    # I accidentally overwrote the object context for the banana measurements:
    # change_experiment_jsons({"common_name": "banana_ycb", "dataset_id": "011_banana", "dataset": "ycb"},
    #                         directory_to_change,
    #                         "object_context.json",
    #                         lambda x: True,
    #                         replace=True)

    directories_to_change = [
                             "C:/Users/jhart/PycharmProjects/butler/butler/experiments/experiment_2022_04_29_16_51_04",
                             "C:/Users/jhart/PycharmProjects/butler/butler/experiments/experiment_2022_04_29_17_06_08",
                             "C:/Users/jhart/PycharmProjects/butler/butler/experiments/experiment_2022_05_03_15_54_05",
                             "C:/Users/jhart/PycharmProjects/butler/butler/experiments/experiment_2022_05_03_16_59_34",
                             "C:/Users/jhart/PycharmProjects/butler/butler/experiments/experiment_2022_05_03_16_46_16",
                             "C:/Users/jhart/PycharmProjects/butler/butler/experiments/experiment_2022_05_03_14_09_16",
                             ]
    # I want all vision outputs to point to this repository because that's what I used to generate the image outputs
    for dtc in directories_to_change:
        change_experiment_jsons({"repository": "https://github.com/hartvjir/detectron2"},
                                dtc,
                                "measurement.json",
                                lambda x: "at-vision" in x)

