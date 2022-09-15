import formatting, utils, uploading, config
import os

if __name__ == "__main__":
    pass
    # print(os.listdir(config.experiment_directory))
    # exp_dirs = list(
    #     map(lambda x: os.path.join(config.experiment_directory, x), os.listdir(config.experiment_directory))
    # )
    exp_dirs = utils.get_experiment_dirs(use_default_format=False)
    # exp_dirs = utils.get_experiment_dirs(directory="C:/Users/jhart/PycharmProjects/butler/butler/dataset/database_exps", use_default_format=False)
    print(exp_dirs)
    print("Number of experiment dirs: ", len(exp_dirs))
    # exit()
    for exp_dir in exp_dirs:
        formatting.experiment_to_json(exp_dir)
        print(exp_dir)

    # dict_path =
    # uploader.post_measurement(auth_tuple=("jeff", "jeff"),
    #                  endpoint="http://127.0.0.1:8000/rest/",
    #                  dict_path=dict_path)


