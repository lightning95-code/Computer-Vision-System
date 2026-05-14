import cv2
import numpy as np


src_points = np.array([
    [612, 320], # лів верх
    [1967, 320], # прав верх
    [1967, 1720], # прав ниж
    [612, 1720] # лів ниж
], dtype=np.float32)

dst_points = np.array([
    [0, 0], # лів верх
    [460, 0], # прав верх
    [460, 460], # прав ниж
    [0, 460] # лів ниж
], dtype=np.float32)

H = cv2.getPerspectiveTransform(src_points, dst_points)


def pixel_to_mm(x, y):
    pt = np.array([[[x, y]]], dtype=np.float32)
    res = cv2.perspectiveTransform(pt, H)
    return res[0][0]