import cv2
import numpy as np
from transform import pixel_to_mm


# PIPELINE
def run_detection(image_path):

    print("\n========== RUN DETECTION ==========")
    print("IMAGE PATH:", image_path)

    # LOAD IMAGE
    img = cv2.imread(image_path)

    if img is None:
        print("IMG IS NONE")
        return [], None

    print("IMAGE LOADED")
    print("IMG SHAPE:", img.shape)

    # LOAD CALIBRATION
    calib_data = np.load("calibration.npz")

    camera_matrix = calib_data["camera_matrix"]
    dist_coeffs = calib_data["dist_coeffs"]

    print("CALIBRATION LOADED")

    # UNDISTORT
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

    print("UNDISTORT DONE")

    # ROI CROP
    x, y, w_roi, h_roi = roi

    print("ROI:", roi)

    if w_roi > 0 and h_roi > 0:

        undistorted = undistorted[
            y:y + h_roi,
            x:x + w_roi
        ]

        print("ROI CROP APPLIED")

    else:
        print("ROI INVALID -> SKIP CROP")

    # VALIDATE IMAGE
    if undistorted is None:
        print("UNDISTORTED IS NONE")
        return [], None

    if undistorted.size == 0:
        print("UNDISTORTED IMAGE EMPTY")
        return [], None

    img = undistorted.copy()

    print("FINAL IMG SHAPE:", img.shape)
    
    # TO GRAY
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # CLAHE
    clahe = cv2.createCLAHE(
        clipLimit=2,
        tileGridSize=(8, 8)
    )

    img_gray_eq = clahe.apply(img_gray)

    # BLUR
    img_blur = cv2.GaussianBlur(
        img_gray_eq,
        (5, 5),
        1.5
    )

    # HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # RED MASK
    lower_red1 = np.array([0, 80, 50])
    upper_red1 = np.array([10, 255, 255])

    lower_red2 = np.array([165, 70, 40])
    upper_red2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)

    mask = cv2.bitwise_or(mask1, mask2)

    # MORPHOLOGY
    kernel = np.ones((5, 5), np.uint8)

    mask = cv2.dilate(mask, kernel, iterations=1)

    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)


    # EDGES
    edges = cv2.Canny(mask, 50, 150)

    kernel = np.ones((3, 3), np.uint8)

    edges = cv2.dilate(edges, kernel, iterations=1)

    # CONTOURS
    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    print("CONTOURS FOUND:", len(contours))

    piece_id = 1
    fanuc_objects = []

    # PROCESS CONTOURS
    for cnt in contours:

        area = cv2.contourArea(cnt)

        if area < 500:
            continue

        (x, y), r = cv2.minEnclosingCircle(cnt)

        x = int(x)
        y = int(y)
        r = int(r)

        # CIRCULARITY
        perimeter = cv2.arcLength(cnt, True)

        if perimeter == 0:
            continue

        circularity = (
            4 * np.pi * area
        ) / (
            perimeter * perimeter
        )

        if circularity < 0.55:
            continue

        # ROI
        y1 = max(y - r, 0)
        y2 = min(y + r, img.shape[0])

        x1 = max(x - r, 0)
        x2 = min(x + r, img.shape[1])

        roi = img_gray[y1:y2, x1:x2]

        if roi.shape[0] == 0 or roi.shape[1] == 0:
            continue

        # CENTER MASK
        mask_center = np.zeros(
            roi.shape[:2],
            dtype=np.uint8
        )

        center_x = roi.shape[1] // 2
        center_y = roi.shape[0] // 2

        center_r = int(min(roi.shape[:2]) * 0.18)

        cv2.circle(
            mask_center,
            (center_x, center_y),
            center_r,
            255,
            -1
        )

        # HSV ROI
        roi_bgr = img[y1:y2, x1:x2]

        if roi_bgr.size == 0:
            continue

        roi_hsv = cv2.cvtColor(
            roi_bgr,
            cv2.COLOR_BGR2HSV
        )

        v_channel = roi_hsv[:, :, 2]

        pixels = v_channel[
            mask_center == 255
        ]

        if pixels.size == 0:
            continue

        mean_val = np.mean(pixels)

        # COLOR
        letter = "B" if mean_val > 140 else "W"

        print(
            f"OBJECT {piece_id}:",
            f"x={x}",
            f"y={y}",
            f"type={letter}"
        )

        # DRAW
        cv2.circle(
            img,
            (x, y),
            r,
            (0, 255, 0),
            2
        )

        cv2.circle(
            img,
            (x, y),
            2,
            (0, 0, 255),
            3
        )

        label = f"{piece_id}{letter}"

        if letter == "W":
            text_color = (255, 255, 255)
            bg_color = (0, 120, 255)
        else:
            text_color = (0, 0, 0)
            bg_color = (255, 200, 0)

        font = cv2.FONT_HERSHEY_SIMPLEX

        font_scale = 1.0
        thickness = 2

        (text_w, text_h), baseline = cv2.getTextSize(
            label,
            font,
            font_scale,
            thickness
        )

        cv2.rectangle(
            img,
            (x + 5, y - text_h - 10),
            (x + 5 + text_w, y - 5),
            bg_color,
            -1
        )

        cv2.putText(
            img,
            label,
            (x + 5, y - 5),
            font,
            font_scale,
            text_color,
            thickness,
            cv2.LINE_AA
        )

        # PIXEL -> MM
        mm_point = pixel_to_mm(x, y)

        if np.isnan(mm_point).any():
            continue

        z_mm = 40.0

        fanuc_data = {
            "id": piece_id,
            "x_mm": float(mm_point[0]),
            "y_mm": float(mm_point[1]),
            "z_mm": z_mm,
            "type": letter
        }

        fanuc_objects.append(fanuc_data)

        piece_id += 1

    print("FINAL OBJECTS:", len(fanuc_objects))

    # RESULT
    return fanuc_objects, img