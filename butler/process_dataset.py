import json
import re
import numpy as np
import os
from typing import Union
import csv
import time

import config


class DataUnit:
    sensor = ""  # type: str
    measurement_parameters = dict()  # type: dict
    sensor_data = dict()  # type: dict
    measured_object = dict()  # type: dict


class DataSet:
    data_loaders = list()  # type: list


top_dict = {}
#
# measurement = {}
# object_instance = {}
# setup = {}
# sensor_outputs = {}
# grasp = {}
# gripper_pose = {}
# object_pose = {}
#
# measurement["object_instance"] = object_instance
# measurement["setup"] = setup
# measurement["sensor_outputs"] = sensor_outputs
# measurement["grasp"] = grasp
# measurement["gripper_pose"] = gripper_pose
# measurement["object_pose"] = object_pose
#
# entry = {}
# values = {}
# entry["values"] = values
#
# top_dict["measurement"] = measurement
# top_dict["entry"] = entry


def register_get_data_functions(*args):
    for f in args:
        # data functions should return:
        # {
        #   "sensor": "sensor_name",
        #   "measurement_parameters": {
        #     "param1": "value1",
        #     ...
        #   },
        #   "sensor_data": {
        #     "quantity1": list or file path,
        #     ...
        #   },
        #   "measured_object": {
        #     "dataset": abc,
        #     "dataset_id": cba,
        #     "maker": xyz,
        #     "common_name": zyx,
        #     "other": "json string"
        #   }
        # }
        pass


def populate_sensor_outputs(file_path, sensor_outputs, quantities):
    with open(file_path, 'r') as f:
        lines = f.readlines()
        for q in quantities:  # type: str
            sensor_outputs[q] = list()
        for line in lines:
            processed_line = line.replace(r"\n", "").split()
            for v, q in zip(processed_line, quantities):  # type: str
                sensor_outputs[q].append(float(v))


gt_results = {
    "RP1725_L41_v1.csv": {
        "entries": [
            {"values": [{"value": 6040, "units": "Pa", "std": 420, "name": "elasticity"}],
             "type": "continuous",
             "name": "elasticity",
             "repository": None
             },
            {"values": [{"value": 513, "units": "N/m", "std": 33, "name": "stiffness"}],
             "type": "continuous",
             "name": "elasticity",
             "repository": None
             }
        ]
    },
    "RP1725_L41_v10.csv": {
        "entries": [
            {"values": [{"value": 6770, "units": "Pa", "std": 680, "name": "elasticity"}],
             "type": "continuous",
             "name": "elasticity",
             "repository": None,
             "ground_truth": True
             },
            {"values": [{"value": 575, "units": "N/m", "std": 58, "name": "stiffness"}],
             "type": "continuous",
             "name": "elasticity",
             "repository": None,
             "ground_truth": True
             }
        ]
    },
    "RP1725_L41_v30.csv": {
        "entries": [
            {"values": [{"value": 7020, "units": "Pa", "std": 710, "name": "elasticity"}, ],
             "type": "continuous",
             "name": "elasticity",
             "repository": None,
             "ground_truth": True
             },
            {"values": [{"value": 596, "units": "N/m", "std": 60, "name": "stiffness"}],
             "type": "continuous",
             "name": "elasticity",
             "repository": None,
             "ground_truth": True
             }
        ]
    },
    "RP1725_L41_v50.csv": {
        "entries": [
            {"values": [{"value": 7160, "units": "Pa", "std": 690, "name": "elasticity"}, ],
             "type": "continuous",
             "name": "elasticity",
             "repository": None,
             "ground_truth": True
             },
            {"values": [{"value": 608, "units": "N/m", "std": 58, "name": "stiffness"}],
             "type": "continuous",
             "name": "elasticity",
             "repository": None,
             "ground_truth": True
             }
        ]
    }
}


def process_single_grasp_professional(parent_dir, file_name: str):
    # print("file_name: ", file_name)
    with open(os.path.join(parent_dir, file_name), "r") as fp:
        l = csv.reader(fp)
        # print(list(l))
        l = np.array(list(l))
        object_parameters = l[0,0].split("_")
        # print(object_parameters)
        object_instance = {"common_name": object_parameters[0].lower(), "object_size": object_parameters[1][1:]+" mm"}
        parameters = {"closing_speed": object_parameters[2][1:]+" mm/s"}
        if len(object_parameters) == 4:
            parameters["opening_speed"] = object_parameters[3]+" mm/s"
        sensor_outputs = {"parameters": parameters}
        measurement = {"object_instance": object_instance, "sensor_outputs": sensor_outputs}
        setup = {"gripper": "professional"}
        measurement["setup"] = setup
        measurement["ground_truth"] = True
        ret = {"measurement": measurement}
        if file_name in gt_results:
            ret["entries"] = gt_results[file_name]
        # print(l.shape)
        sensor_outputs["professional"] = dict()
        professional_output = sensor_outputs["professional"]
        for i in range(8):
            professional_output[l[1,i]+" ["+l[2,i]+"]"] = l[3:,i].tolist()
        with open(
                os.path.join(config.upload_dicts_directory, "upload_dict_" + os.path.splitext(file_name)[0] + ".json"),
                "w") as fp:
            json.dump(obj=ret, fp=fp)
        print("processed: ", file_name)


def process_single_grasp_barrett_hand(parent_dir, file_name: str):
    file_name_split = file_name.split("-")
    abs_path = os.path.join(parent_dir, file_name)
    npz = np.load(abs_path, allow_pickle=True)
    # print(npz.__dict__)
    finger_configuration = "opposing_fingers" if file_name[:2] == "a1" else "same_side_fingers"
    velocity = file_name[3:6]+" rad/s"
    meas_sub_dict = {
        "object_instance": {
            "common_name": file_name_split[1].lower()
        },
        "sensor_outputs": {
            "parameters": {
                "velocity": velocity,
                "finger_configuration": finger_configuration
            }
        },
        "setup": {
            "gripper":  "barret_hand"
        }
    }
    ret = {"measurement": meas_sub_dict}
    sensor_outputs = meas_sub_dict["sensor_outputs"]
    sensor_outputs["barret_hand"] = dict()
    barret_output = sensor_outputs["barret_hand"]
    for f in npz.files:
        # print(f)
        # print(npz[f].shape)
        barret_output[f] = npz[f].tolist()
    npz.close()
    with open(os.path.join(config.upload_dicts_directory, "upload_dict_" + os.path.splitext(file_name)[0] + ".json"), "w") as fp:
        json.dump(obj=ret, fp=fp)
    print("processed: ", file_name)


def process_single_grasp_rg6(parent_dir, file_name):
    # print(os.path.join(parent_dir, file_name))
    file_name_split = file_name.split()  # type: list[str]
    meas_sub_dict = {
        "object_instance": {
            "common_name": file_name_split[0].lower()
        },
        "sensor_outputs": {
            "parameters": {
                "max_force": file_name_split[1]
            }
        },
        "setup": {
            "gripper":  "onrobot_rg6"
        }
    }
    ret = {"measurement": meas_sub_dict}

    file_path = os.path.join(parent_dir, file_name)
    sensor_outputs = meas_sub_dict["sensor_outputs"]
    sensor_outputs["onrobot_rg6"] = dict()
    rg6_outputs = sensor_outputs["onrobot_rg6"]
    quantities = SingleGraspDataset.onrobot_rg_6_quantities
    populate_sensor_outputs(file_path, rg6_outputs, quantities)

    with open(os.path.join(config.upload_dicts_directory, "upload_dict_"+os.path.splitext(file_name)[0]+".json"), "w") as f:
        json.dump(obj=ret, fp=f)
    print("processed: ", file_name)


def process_single_grasp_qb_softhand(parent_dir, file_name):
    # print(os.path.join(parent_dir, file_name))
    file_name_split = file_name.split()  # type: list[str]
    meas_sub_dict = {
        "object_instance": {
            "common_name": file_name_split[0].lower()
        },
        "sensor_outputs": {
        },
        "setup": {
            "gripper":  "qb_softhand"
        }
    }
    ret = {"measurement": meas_sub_dict}

    file_path = os.path.join(parent_dir, file_name)
    sensor_outputs = meas_sub_dict["sensor_outputs"]
    sensor_outputs["qb_softhand"] = dict()
    qb_output = sensor_outputs["qb_softhand"]
    quantities = SingleGraspDataset.qb_softhand_quantities
    populate_sensor_outputs(file_path, qb_output, quantities)
    if len(qb_output["position"]) < 23:
        parameters = {"closing_time": "2.5s"}
    else:
        parameters = {"closing_time": "1.5s"}
    sensor_outputs["parameters"] = parameters

    with open(os.path.join(config.upload_dicts_directory, "upload_dict_"+os.path.splitext(file_name)[0]+".json"), "w") as f:
        json.dump(obj=ret, fp=f)
    print("processed: ", file_name)


def process_single_grasp_robotiq_2f85(parent_dir, file_name):
    # print(os.path.join(parent_dir, file_name))
    file_name_split = file_name.split("-")  # type: list[str]
    meas_sub_dict = {
        "object_instance": {
            "common_name": file_name_split[-2].lower()
        },
        "sensor_outputs": {
            "parameters": {
                "closing_speed": file_name_split[-1].split("s")[0]
            }
        },
        "setup": {
            "gripper":  "robotiq_2f85"
        }
    }
    ret = {"measurement": meas_sub_dict}

    file_path = os.path.join(parent_dir, file_name)
    sensor_outputs = meas_sub_dict["sensor_outputs"]
    sensor_outputs["robotiq_2f85"] = dict()
    robotiq_output = sensor_outputs["robotiq_2f85"]
    quantities = SingleGraspDataset.robotiq_2f85_quantities
    populate_sensor_outputs(file_path, robotiq_output, quantities)

    with open(os.path.join(config.upload_dicts_directory, "upload_dict_"+os.path.splitext(file_name)[0]+".json"), "w") as f:
        json.dump(obj=ret, fp=f)
    print("processed: ", file_name)


def process_rg6_type(file_name, has_object_line=True, selected_data_columns=np.array([1, 2]), printable=False, has_value_line=True, value_names=None):
    """
    // object={obj_name}
    //prop1 prop2 ...
    """
    # object_name
    with open(file_name, "r") as f:
        if has_object_line:
            object_line = f.readline()
            lll = re.search(r"object=\s*[^\s]+", object_line)
            object_name = lll.group().replace(" ", "").replace("object=", "")
            # print("object_name", object_name)

        if has_value_line:
            value_line = f.readline()
            # remove spaces, remove slashes, remove newline
            value_names = list(filter(lambda x: len(x) != 0, value_line.replace("/", "").replace("\n", "").split(" ")))
            # print("value_names", value_names)
            if isinstance(value_line, str):
                value_names = list(filter(lambda x: len(x) != 0, value_line.replace("/", "").replace("\n", "").split(" ")))
            else:
                raise TypeError("value_line has to be of type `str` and format \"quantity_1 quantity_2 ... quantity_n\", value_line: "+str(value_line))

        data_lines = list(map(lambda x: x.replace("\n", "").split(), f.readlines()))
        # i guess this is how far i go without numpy
        num_lines = len(data_lines)
        assert num_lines != 0, "The data must have at least one row! File: "+file_name
        data_columns = np.transpose(data_lines)

        selected_data = data_columns[selected_data_columns]
        # print("data_lines", np.shape(data_lines))
        # print("data_columns", np.shape(data_columns))
        # print(data_columns)
        # print("selected_data", selected_data)
        data_dict = {}
        for k,i in enumerate(selected_data_columns):
            data_dict[value_names[i]] = np.array(selected_data[k])
            if not printable:
                data_dict[value_names[i]] = data_dict[value_names[i]].tolist()
        # print(data_dict.keys())
        # old_object_str = lll.group()
        # while object_str != old_object_str:
        #     old_object_str = object_str
        #     object_str = object_str.replace(" ", "")
    return data_dict


def process_file_folder_rg6(folder, file_name, dataset="elasticity_estimation", sensor="onrobot_rg6", printable=False):
    setup = {"gripper": sensor}
    measurement_templates = {}  # template per folder
    measurement_template = {}
    measurement_templates[file_name] = measurement_template
    measurement_template["object_context"] = {}
    object_context = measurement_template["object_context"]
    common_names = {"kinovacube": "white_kinova_cube_light"}  # FIXME: THIS USES ALREADY EXISTING NAMES => check the database
    object_context["common_name"] = file_name.lower() if common_names.get(file_name) is None else common_names.get(file_name).lower()
    # object_context["dataset_id"] = file_name
    object_context["dataset"] = dataset
    object_context["other"] = {}
    # TODO: measurement parameters in the database, e.g. gripper closing speed absolute, gripper closing speed relative
    # print(object_context)

    on_folder = os.path.join(folder, file_name)
    ls_measurement_folder = os.listdir(on_folder)
    for measurement_file in ls_measurement_folder:
        # print(measurement_file)
        abs_file_path = os.path.join(on_folder, measurement_file)
        measurement_dict = {}
        measurement_dict["object_instance"] = object_context
        data_dict = process_rg6_type(abs_file_path, printable=printable)
        measurement_dict["sensor_outputs"] = {}
        sensor_output_dict = measurement_dict["sensor_outputs"]
        sensor_output_dict[sensor] = data_dict
        parameter_value = re.search("[^-]+[.]txt$", measurement_file).group().replace(".txt", "")
        object_context["other"]["object_size"] = parameter_value + "mm"  # FIXME: THIS IS SPECIFIC FOR RG6

        # setup
        measurement_dict["setup"] = setup
        ret = {"measurement": measurement_dict}
        # print(measurement_dict)
        # return ret
        with open(os.path.join(config.upload_dicts_directory, "upload_dict_"+os.path.splitext(os.path.basename(abs_file_path))[0]+".json"), "w") as f:
            json.dump(obj=ret, fp=f)
        print("processed: ", measurement_file)


def process_file_folder_2f85(folder, dataset="elasticity_estimation", sensor="robotiq_2f85", measurement_parameters=None, printable=False):
    setup = {"gripper": sensor}
    ls_folder = os.listdir(folder)
    object_names = ls_folder  # its the same in this case
    object_contexts = {}
    measurement_templates = {}  # template per folder
    for on in object_names:
        measurement_template = {}
        measurement_templates[on] = measurement_template
        measurement_template["object_context"] = {}
        object_context = measurement_template["object_context"]
        common_names = {"kinovacube": "white_kinova_cube_light"}  # FIXME: THIS USES ALREADY EXISTING NAMES => check the database
        object_context["common_name"] = on if common_names.get(on) is None else common_names.get(on)
        object_context["dataset_id"] = on
        object_context["dataset"] = dataset
        object_context["other"] = {}
        # TODO: measurement parameters in the database, e.g. gripper closing speed absolute, gripper closing speed relative
        # print(object_context)

        on_folder = os.path.join(folder, on)
        ls_measurement_folder = os.listdir(on_folder)
        for measurement_file in ls_measurement_folder:
            ret = {}
            abs_file_path = os.path.join(on_folder, measurement_file)
            measurement_dict = {}
            measurement_dict["object_instance"] = object_context
            data_dict = process_rg6_type(abs_file_path, has_object_line=False, selected_data_columns=[0,1,2], printable=printable)
            measurement_dict["sensor_outputs"] = {}
            sensor_output_dict = measurement_dict["sensor_outputs"]
            data_dict["parameters"] = measurement_parameters
            sensor_output_dict[sensor] = data_dict
            parameter_value = measurement_file.split("-")[-2]
            object_context["other"]["object_size"] = parameter_value + "mm"  # FIXME: THIS IS SPECIFIC FOR RG6
            # print(measurement_dict)

            # setup
            measurement_dict["setup"] = setup
            ret = {"measurement": measurement_dict}
            with open(os.path.join(config.upload_dicts_directory, "upload_dict_"+os.path.splitext(os.path.basename(abs_file_path))[0]+".json"), "w") as f:
                json.dump(obj=ret, fp=f)
            print("processed: ", measurement_file)
    return ret


def folder_name_to_parameters_rg6(folder_name: str):
    under_split = folder_name.split("_")
    # print("re.search(\"^[^_]+\", folder_name).group()", re.search("^[^_]+", folder_name).group())
    replace_last__ = lambda x: re.sub("_+$", "", x)
    param_units = [replace_last__(x.group()[1:]) for x in re.finditer(r"[\d][a-zA-Z_]+", folder_name)]
    param_values = [x.group() for x in re.finditer(r"[+-]?([0-9]*[.])?[0-9]+", folder_name)]
    param_name = replace_last__(re.search("[a-zA-Z]+_", folder_name).group())
    # print(param_name)
    # print(list(zip(param_values, param_units)))
    ret = {}
    # clos
    for v,u in zip(param_values, param_units):
        ret[param_name+"_"+u.replace("_", "/")] = v
    # print(ret)
    # print(re.search(r"[+-]?([0-9]*[.])?[0-9]+", folder_name).group())
    return ret


def process_parameter_folder_2f85(top_folder, parameter_folder, dataset="elasticity_estimation", sensor="robotiq_2f85", measurement_parameters=None, printable=False):
    ret = {}
    measurement_parameters = folder_name_to_parameters_rg6(parameter_folder)
    processed_measurements = process_file_folder_2f85(os.path.join(top_folder, parameter_folder), measurement_parameters=measurement_parameters, printable=printable)
    for p in processed_measurements:
        ret[p] = processed_measurements[p]
    # print(parameter_folder, measurement_parameters)
    # return ret


def replace_values(abs_file_path):
    with open(abs_file_path, "r+") as fp:
        disk_dict = json.load(fp)
        if "grasped" in disk_dict.get("values", {}):
            if "grasped" in disk_dict["gripper_pose"] or "grasped" in disk_dict["grasp"]:
                del disk_dict["values"]
        elif "volume" in disk_dict.get("values", {}):
            values = disk_dict["values"]
            disk_dict["params"] = dict()
            disk_dict["params"]["mean"] = values["volume"]
            disk_dict["params"]["sigma"] = values["volume"]*0.3
            del disk_dict["values"]
        fp.seek(0)
        fp.truncate(0)
        json.dump(obj=disk_dict, fp=fp)
    print("processed:", abs_file_path)


class SingleGraspDataset:
    robotiq_2f85_quantities = ["position", "current_relative"]
    robotiq_2f85_parameters = ["velocity %", "velocity mm/s"]
    qb_softhand_quantities = ["position", "current"]
    onrobot_rg_6_quantities = ["position", "current"]
    onrobot_rg_6_parameters = ["velocity mm/s", "threshold"]
    barrett_hand_quantities = ["pressure", "torque", "coordinates"]
    barrett_hand_parameters = ["velocity rad/s", "velocity mm/s"]
    action = lambda x,y: (x,y)

    folder_structure = {
        # "Single_grasp_deformable_object_discrimination": {
        #     "Barrett Hand": {
        #         "all": {  # Foams & Objects
        #             "all": {  # folder "all" in Foams and all folders in Objects
        #                 "trn":  process_single_grasp_barrett_hand,  # apply action to this dir
        #                 "val":  process_single_grasp_barrett_hand,  # apply action to this dir
        #                 "test": process_single_grasp_barrett_hand,  # apply action to this dir
        #             }
        #         }
        #     },
        #     "Onrobot RG 6": {
        #         "all": {  # Foams & Objects
        #             "all": {  # folder "all" in Foams and Objects
        #                 "trn":  process_single_grasp_rg6,  # apply action to this dir
        #                 "val":  process_single_grasp_rg6,  # apply action to this dir
        #                 "test": process_single_grasp_rg6,  # apply action to this dir
        #             }
        #         }
        #     },
        #     "qb SoftHand": {
        #         "all": {  # Foams & Objects
        #             "all": {  # folder "all" in Foams and Objects
        #                 "trn":  process_single_grasp_qb_softhand,  # apply action to this dir
        #                 "val":  process_single_grasp_qb_softhand,  # apply action to this dir
        #                 "test": process_single_grasp_qb_softhand,  # apply action to this dir
        #             }
        #         }
        #     },
        #     "Robotiq 2F85": {
        #         "all": {  # Foams & Objects
        #             "all": {  # folder "all" in Foams and Objects
        #                 "trn":  process_single_grasp_robotiq_2f85,  # apply action to this dir
        #                 "val":  process_single_grasp_robotiq_2f85,  # apply action to this dir
        #                 "test": process_single_grasp_robotiq_2f85,  # apply action to this dir
        #             }
        #         }
        #     },
        # },
        "pliska_dataset": {
            "Barrett Hand": process_single_grasp_barrett_hand,  # apply action to this dir
            "Onrobot RG 6": process_single_grasp_rg6,  # apply action to this dir
            "qb SoftHand": process_single_grasp_qb_softhand,  # apply action to this dir
            "Robotiq 2F85": process_single_grasp_robotiq_2f85,  # apply action to this dir
        },
        "Squeezing": {
            "squeezing_data": {
                "Onrobot_RG6": {
                    "Mixed-set": process_file_folder_rg6
                },
                "Robotiq_2F-85": {
                    "Mixed-set": process_parameter_folder_2f85
                },
                "Professional_Setup": {
                    "CSV": process_single_grasp_professional
                }
            }
        },
        # "database_exps": {
        #     "all": {
        #         "all": {
        #             "data": {
        #                 "measurement.json": replace_values
        #             }
        #         }
        #     }
        # }
    }
    # top_folder = "C:/Users/jhart/PycharmProjects/butler/butler/dataset/"

    # def __init__(self, top_folder):
    #     self.top_folder = top_folder

    def process_dataset(self, parent_dir: str, folders: Union[dict, callable]):
        start_time = time.time()
        assert isinstance(parent_dir, str), "parent_dir argument must be a string"
        assert not isinstance(folders, classmethod) and not isinstance(folders, staticmethod), "static or class methods are not callable on their own! Use lambda or def"
        # assert isinstance(folders, dict), "folders must be a dictionary hierarchy of the directories of the dataset"
        print(parent_dir, folders)
        if callable(folders):
            if os.path.isdir(parent_dir):
                ls_parent_dir = os.listdir(parent_dir)
                for p in ls_parent_dir:
                    folders(parent_dir, p)
            else:
                folders(parent_dir)
        elif "all" in folders and len(folders) == 1:
            all_path = os.path.join(parent_dir, "all")
            if os.path.isdir(all_path):
                self.process_dataset(all_path, folders["all"])  # os.listdir(all_path))
            else:
                ls_parent_dir = os.listdir(parent_dir)
                for d in ls_parent_dir:
                    new_p = os.path.join(parent_dir, d)
                    if os.path.isdir(new_p):
                        self.process_dataset(new_p, folders["all"])
        else:
            for d in folders:
                abs_path = os.path.join(parent_dir, d).replace("\\", "/")
                # if os.path.isdir(abs_path):
                # doesnt have to be a directory when we want to apply the function to one file
                self.process_dataset(abs_path, folders[d])
        print("time taken: ", time.time() - start_time)


if __name__ == "__main__":
    sg = SingleGraspDataset()
    sg.process_dataset(parent_dir=r"C:/Users/jhart/PycharmProjects/butler/butler/dataset/", folders=SingleGraspDataset.folder_structure)
