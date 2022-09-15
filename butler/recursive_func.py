import os
import time
from typing import *


class ProcessFolders:

    # def __init__(self, top_folder):
    #     self.top_folder = top_folder

    def process_dataset(self, abs_parent_dir_or_file: str, folders_or_func: Union[dict, callable]):
        start_time = time.time()
        assert isinstance(abs_parent_dir_or_file, str), "parent_dir argument must be a string"
        assert not isinstance(folders_or_func, classmethod) and not isinstance(folders_or_func, staticmethod), "static or class methods are not callable on their own! Use lambda or def"
        # assert isinstance(folders, dict), "folders must be a dictionary hierarchy of the directories of the dataset"
        # print(abs_parent_dir_or_file, folders_or_func)
        if callable(folders_or_func):
            if os.path.isdir(abs_parent_dir_or_file):
                ls_parent_dir = os.listdir(abs_parent_dir_or_file)
                for p in ls_parent_dir:
                    folders_or_func(abs_parent_dir_or_file, p)
            else:
                folders_or_func(abs_parent_dir_or_file)
        elif "all" in folders_or_func and len(folders_or_func) == 1:
            all_path = os.path.join(abs_parent_dir_or_file, "all")
            if os.path.isdir(all_path):
                self.process_dataset(all_path, folders_or_func["all"])  # os.listdir(all_path))
            else:
                ls_parent_dir = os.listdir(abs_parent_dir_or_file)
                for d in ls_parent_dir:
                    new_p = os.path.join(abs_parent_dir_or_file, d)
                    if os.path.isdir(new_p):
                        self.process_dataset(new_p, folders_or_func["all"])
        else:
            for d in folders_or_func:
                abs_path = os.path.join(abs_parent_dir_or_file, d).replace("\\", "/")
                # if os.path.isdir(abs_path):
                # doesnt have to be a directory when we want to apply the function to one file
                self.process_dataset(abs_path, folders_or_func[d])
        # print("time taken: ", time.time() - start_time)


if __name__ == "__main__":

    your_function = lambda x: print(x, "\n", os.path.dirname(x), "\n", os.path.join(os.path.dirname(x), "the_result.json"))
    folder_structure = {
        # e.g. */*/data/recording.wav
        "all": {
            "all": {
                "data": {
                    # calls your_function on each recording.wav like so:
                    #  your_function(abs_path_to_recording_wav)
                    "recording.wav": your_function
                }
            }
        }
    }
    top_folder = "C:/Users/jhart/Downloads/experiments/experiment_17_objects_clean"
    process_class = ProcessFolders()
    process_class.process_dataset(top_folder, folder_structure)






