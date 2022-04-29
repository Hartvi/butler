import formatting, utils

if __name__ == "__main__":
    pass
    exp_dirs = utils.get_all_experiment_dirs()
    for exp_dir in exp_dirs:
        formatting.experiment_to_json(exp_dir)
        print(exp_dir)
    # dict_path =
    # uploader.post_measurement(auth_tuple=("jeff", "jeff"),
    #                  endpoint="http://127.0.0.1:8000/rest/",
    #                  dict_path=dict_path)


