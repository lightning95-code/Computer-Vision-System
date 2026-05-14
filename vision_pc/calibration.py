#!/usr/bin/env python3

import cv2
import numpy as np
import glob
import os

# BASE PATH 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CHECKERBOARD = (7, 7)

criteria = (
    cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
    50,
    0.0001
)

objpoints3D = []
imgpoints2D = []

objp = np.zeros((CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
objp[:, :2] = np.mgrid[
    0:CHECKERBOARD[0],
    0:CHECKERBOARD[1]
].T.reshape(-1, 2)

# PATHS
OUTPUT_DIR = os.path.join(BASE_DIR, "output_corners")
CALIB_DIR = os.path.join(BASE_DIR, "calibration_images")

os.makedirs(OUTPUT_DIR, exist_ok=True)

log_file = open(os.path.join(BASE_DIR, "calibration_log.txt"), "w")

images = glob.glob(os.path.join(CALIB_DIR, "*.*"))

print("\n")
print("Знайдено зображень:", len(images))
print("\n")

log_file.write(f"Знайдено зображень: {len(images)}\n")

good = 0
bad = 0
img_size = None


# MAIN LOOP
for fname in images:

    img = cv2.imread(fname)

    if img is None:
        print("Не вдалося відкрити файл:", fname)
        log_file.write(f"Не вдалося відкрити файл: {fname}\n")
        continue

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    ret, corners = cv2.findChessboardCornersSB(
        gray,
        CHECKERBOARD,
        cv2.CALIB_CB_EXHAUSTIVE + cv2.CALIB_CB_ACCURACY
    )

    if not ret:
        flags = (
            cv2.CALIB_CB_ADAPTIVE_THRESH +
            cv2.CALIB_CB_NORMALIZE_IMAGE
        )

        ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, flags)

    print("\n------------------------------")
    print("Файл:", fname)
    print("Результат:", ret)

    if ret:
        print("Розмір кутів:", corners.shape)
        print("Тип даних:", corners.dtype)
    else:
        print("!!! Шахівницю не знайдено")

    log_file.write(f"{fname} -> знайдено: {ret}\n")

    # EXACT SAME VISUAL LOGIC
    if ret:

        corners = np.asarray(corners, dtype=np.float32)

        if corners.shape[1] == 2:
            corners = corners.reshape(-1, 1, 2)

        corners2 = cv2.cornerSubPix(
            gray,
            corners,
            (11, 11),
            (-1, -1),
            criteria
        )

        objpoints3D.append(objp.copy())
        imgpoints2D.append(corners2)

        good += 1

        vis = img.copy()

        for corner in corners2:
            x, y = corner.ravel()
            cv2.circle(vis, (int(x), int(y)), 10, (0, 0, 255), -1)

        cv2.drawChessboardCorners(vis, CHECKERBOARD, corners2, True)

        cv2.imwrite(
            os.path.join(OUTPUT_DIR, os.path.basename(fname)),
            vis
        )

        cv2.namedWindow('DEBUG CORNERS', cv2.WINDOW_NORMAL)
        cv2.imshow("DEBUG CORNERS", vis)
        cv2.waitKey(0)

    else:
        bad += 1

    if img_size is None:
        h, w = gray.shape[:2]
        img_size = (w, h)

    cv2.namedWindow('Photo', cv2.WINDOW_NORMAL)
    cv2.imshow('Photo', img)
    cv2.waitKey(0)

cv2.destroyAllWindows()

# SUMMARY
print("\n")
print("Успішно оброблено зображень:", good)
print("Неуспішно оброблено зображень:", bad)
print("Розмір зображення:", img_size)
print("\n")

log_file.write(f"\nУспішно оброблено: {good}\n")
log_file.write(f"Неуспішно оброблено: {bad}\n")

if good < 5:
    print("Недостатньо якісних зображень для калібрування!")
    log_file.close()
    exit()

# CALIBRATION
ret, matrix, distortion, rvecs, tvecs = cv2.calibrateCamera(
    objpoints3D,
    imgpoints2D,
    img_size,
    None,
    None
)

print("\nМАТРИЦЯ КАМЕРИ")
print(matrix)

print("\nКОЕФІЦІЄНТИ ДИСТОРСІЇ")
print(distortion)

print("\nRMS ПОХИБКА (OpenCV):")
print(ret)

log_file.write("\nМатриця камери:\n" + str(matrix))
log_file.write("\nКоефіцієнти дисторсії:\n" + str(distortion))
log_file.write(f"\nRMS похибка: {ret}\n")

fx = matrix[0, 0]
fy = matrix[1, 1]
cx = matrix[0, 2]
cy = matrix[1, 2]

print("Фокус X (fx):", fx)
print("Фокус Y (fy):", fy)
print("Головна точка X (cx):", cx)
print("Головна точка Y (cy):", cy)

# REPROJECTION ERROR
total_error = 0

for i in range(len(objpoints3D)):
    projected, _ = cv2.projectPoints(
        objpoints3D[i],
        rvecs[i],
        tvecs[i],
        matrix,
        distortion
    )

    error = cv2.norm(imgpoints2D[i], projected, cv2.NORM_L2) / len(projected)
    total_error += error

mean_error = total_error / len(objpoints3D)

print("\nПохибка репроєкції:", mean_error)

if mean_error < 0.3:
    print("Якість: ВІДМІННА")
elif mean_error < 0.5:
    print("Якість: ДОБРА")
else:
    print("Якість: ПОГАНА")

log_file.write(f"\nПохибка репроєкції: {mean_error}\n")

# SAVE FILES
np.savez(
    os.path.join(BASE_DIR, "calibration.npz"),
    camera_matrix=matrix,
    dist_coeffs=distortion
)

np.save(
    os.path.join(BASE_DIR, "reprojection_error.npy"),
    mean_error
)

log_file.write("\nЗбережено calibration.npz\n")
log_file.write("Збережено reprojection_error.npy\n")

log_file.close()

print("\nЗбережені файли:")
print("- calibration.npz")
print("- reprojection_error.npy")
print("- calibration_log.txt")
print("- output_corners/")