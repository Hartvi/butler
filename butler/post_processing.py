import json
import os

import utils


def change_experiment_jsons(update_dict, experiment_directory, json_file_name, rule, replace=False):
    """"""
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
    directory_to_change = "C:/Users/jhart/PycharmProjects/butler/butler/experiments/experiment_enamel_mug_ycb"
    # I forgot to change the object context before the measurement:
    # change_experiment_jsons({"dataset_id": "025_mug", "common_name": "enamel_mug_ycb"},
    #                         directory_to_change,
    #                         "object_context.json",
    #                         lambda x: True)

    # I forgot to shit the z up by 5:
    # directory_to_change = "C:/Users/jhart/PycharmProjects/butler/butler/experiments/experiment_banana_ycb"
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
                             "C:/Users/jhart/PycharmProjects/butler/butler/experiments/experiment_banana_ycb",
                             "C:/Users/jhart/PycharmProjects/butler/butler/experiments/experiment_banana",
                             "C:/Users/jhart/PycharmProjects/butler/butler/experiments/experiment_enamel_mug_ycb",
                             "C:/Users/jhart/PycharmProjects/butler/butler/experiments/experiment_wineglass_ycb",
                             "C:/Users/jhart/PycharmProjects/butler/butler/experiments/experiment_wooden_box_ycb",
                             "C:/Users/jhart/PycharmProjects/butler/butler/experiments/experiment_plastic_cup_ycb",
                             ]
    # I want all vision outputs to point to this repository because that's what I used to generate the image outputs
    # for dtc in directories_to_change:
    #     change_experiment_jsons({"repository": "https://github.com/hartvjir/detectron2"},
    #                             dtc,
    #                             "measurement.json",
    #                             lambda x: "at-vision" in x)
    white_kinova_dir = "/unused/experiments/experiments/experiment_white_kinova_cube_light"
    white_kinova_context = {"common_name": "white_kinova_cube_light"}
    change_experiment_jsons(white_kinova_context,
                            white_kinova_dir,
                            "object_context.json",
                            lambda x: "data" in x,
                            replace=True)

