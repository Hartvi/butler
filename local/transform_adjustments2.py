from __future__ import print_function, division

import numpy as np
from scipy.spatial.transform import Rotation as R



def adjust_cosy_pose(r, t):
    """This only works for the middle of the table ~42 cm in front of base.

    Jan isn't here so this is the most we can do at this point in time.
    """
    return r, np.array([t[0], t[1], t[2] + 0.05])


def r_and_t_to_M(r, t):
    M = np.eye(4)
    for i in range(3):
        for j in range(3):
            M[i][j] = r[i][j]
        M[i][3] = t[i]
    return M


def relative_object_to_gripper(M_object, M_gripper):
    return np.matmul(np.linalg.inv(M_object), M_gripper)


def adjusted_object_to_gripper(r_obj, t_obj, r_grip, t_grip):
    r_obj, t_obj = adjust_cosy_pose(r_obj, t_obj)
    M_obj = r_and_t_to_M(r_obj, t_obj)
    M_grip = r_and_t_to_M(r_grip, t_grip)
    return relative_object_to_gripper(M_obj, M_grip)


if __name__ == "__main__":
    r = R.from_euler('xyz', [4.584, -1.095, -88.824], degrees=True)  # obj00004
    t = np.array([0.42, -0.019, -0.013])

    rm = r.as_dcm()
    Mobject = np.eye(4)
    for i in range(3):
        for j in range(3):
            Mobject[i][j] = rm[i][j]
        Mobject[i][3] = t[i]

    # print(np.matmul(Mobject, np.array([[0],[0],[0],[1]])))

    # print(Mobject)

    rgripper = R.from_quat([0.70772, 0.70621, -0.013213, -0.014892])
    # print("gripper euler:", rgripper.as_euler('xyz', degrees=True))
    tgripper = np.array([0.338, 0.01, 0.184])
    rgripperm = rgripper.as_dcm()
    # print(rgripper.as_dcm())

    Mgripper = np.eye(4)
    for i in range(3):
        for j in range(3):
            Mgripper[i][j] = rgripperm[i][j]
        Mgripper[i][3] = tgripper[i]

    # print(np.matmul(Mgripper, np.array([[0],[0],[0],[1]])))
    # print("relative position:", tgripper-t)
    # print("relative position in obj coords:", np.matmul(rm, (tgripper-t)))

    # print("relative rotation from eulers: ", R.from_euler('xyz', rgripper.as_euler('xyz', degrees=True) - np.array([4.584, -1.095, -88.824]), degrees=True).as_dcm())
    # print("delta euler: ", rgripper.as_euler('xyz', degrees=True) - np.array([4.584, -1.095, -88.824]))

    # print("delta euler from matrices: ", np.matmul(rgripperm, rm))

    # print(np.matmul(np.linalg.inv(Mobject), Mgripper))
    adjusted_M = adjusted_object_to_gripper(r.as_dcm(), t, rgripperm, tgripper)
    # print(adjusted_M)
    # print(adjusted_M[:3,:3])
    adjusted_r = R.from_dcm(adjusted_M[:3,:3])
    print(adjusted_M)
    print("adjusted_r:", adjusted_r.as_euler('xyz', degrees=True))
