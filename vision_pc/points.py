import os

import cv2
import numpy as np

img = cv2.imread(r"D:\my diploma\new_img_for_test\chessboard_set_2\board_ref_20260512_151912.png")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
calib_path = os.path.join(BASE_DIR, "calibration.npz")

calib_data = np.load(calib_path)

camera_matrix = calib_data["camera_matrix"]
dist_coeffs = calib_data["dist_coeffs"]


    #  Усунення дисторсії
h, w = img.shape[:2]

new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(
        camera_matrix,
        dist_coeffs,
        (w, h),
        0,
        (w, h)
    )

undistorted = cv2.undistort(
        img,
        camera_matrix,
        dist_coeffs,
        None,
        new_camera_matrix
    )

x, y, w_roi, h_roi = roi
undistorted = undistorted[y:y+h_roi, x:x+w_roi]

img = undistorted.copy()

points = []

def mouse_click(event, x, y, flags, param):
    global points, img

    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))
        print(f"Point: {x}, {y}")

        cv2.circle(img, (x, y), 5, (0, 0, 255), -1)
        cv2.imshow("img", img)

cv2.namedWindow("img", cv2.WINDOW_NORMAL)
cv2.imshow("img", img)
cv2.setMouseCallback("img", mouse_click)

cv2.waitKey(0)
cv2.destroyAllWindows()

print("\nFINAL POINTS:")

for p in points:
    print(p)
if len(points) != 4:
    print("ERROR: потрібно рівно 4 точки (TL, TR, BR, BL)")
    exit()

def order_points(pts):
    pts = np.array(pts, dtype=np.float32)

    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)

    tl = pts[np.argmin(s)]
    br = pts[np.argmax(s)]
    tr = pts[np.argmin(diff)]
    bl = pts[np.argmax(diff)]

    return np.array([tl, tr, br, bl], dtype=np.float32)

src_points = order_points(points)

print("\nORDERED POINTS:")
for p in src_points:
    print(p)