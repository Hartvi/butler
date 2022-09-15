import csv
import numpy as np

numberoflines = 100
fn = "C:/Users/jhart/PycharmProjects/butler/butler/dataset/Squeezing/squeezing_data/Professional_Setup/CSV_Results/RP1725_L41_v1.csv"
fn = "C:/Users/jhart/PycharmProjects/butler/butler/dataset/Squeezing/squeezing_data/Professional_Setup/CSV/V4515_L40_v30_1.6.csv"
with open(fn, "r") as fp:
    l = csv.reader(fp)
    # print(list(l))
    l = np.array(list(l))
    object_parameters = l[0,0].split("_")
    # print(object_parameters)
    object_instance = {"common_name": object_parameters[0], "object_size": object_parameters[1][1:]+" mm"}
    parameters = {"closing_speed": object_parameters[2][1:]+" mm/s"}
    if len(object_parameters) == 4:
        parameters["opening_speed"] = object_parameters[3]+" mm/s"
    sensor_outputs = {"parameters": parameters}
    measurement = {"object_instance": object_instance, "sensor_outputs": sensor_outputs}
    setup = {"gripper": "professional"}
    ret = {"measurement": measurement}
    print(l.shape)
    for i in range(8):
        sensor_outputs[l[1,i]+" ["+l[2,i]+"]"] = l[3:,i]#.tolist()
    print(ret)
    # for r in l:
    #     if numberoflines == 0:
    #         break
    #     numberoflines -= 1
    #     print(r)

