from flask import Flask, request, jsonify, send_file
import os
import cv2
import json

from detection import run_detection
from fanuc_sender import send_to_fanuc

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_PATH = os.path.join(BASE_DIR, "uploads", "input.jpg")
RESULT_PATH = os.path.join(BASE_DIR, "static", "result.jpg")
OBJECTS_PATH = os.path.join(BASE_DIR, "data", "objects.json")

latest_objects = []

print(">>> PC SERVER FILE LOADED <<<")

# PROCESS IMAGE
@app.route('/process', methods=['POST'])
def process():

    print("\n PROCESS START: ")

    global latest_objects

    try:
        if 'image' not in request.files:
            print("NO IMAGE IN REQUEST")
            return jsonify({"error": "no image"}), 400

        file = request.files['image']

        print("FILE RECEIVED")

        file.save(UPLOAD_PATH)

        print("SAVED TO:", UPLOAD_PATH)

        if not os.path.exists(UPLOAD_PATH):
            print("FILE NOT SAVED")
            return jsonify({"error": "file not saved"}), 500

        size = os.path.getsize(UPLOAD_PATH)
        print("FILE SIZE:", size)

        if size == 0:
            print("EMPTY FILE")
            return jsonify({"error": "empty file"}), 500

        img = cv2.imread(UPLOAD_PATH)

        if img is None:
            print("cv2.imread FAILED (corrupt image)")
            return jsonify({"error": "invalid image"}), 500

        print("IMAGE LOADED OK")

        objects, result_img = run_detection(UPLOAD_PATH)

        print("DETECTION DONE, OBJECTS:", len(objects))

        latest_objects = objects

        with open(OBJECTS_PATH, "w", encoding="utf-8") as f:
            json.dump(objects, f, indent=4)

        ok = cv2.imwrite(RESULT_PATH, result_img)

        print("RESULT SAVED:", ok, RESULT_PATH)

        return jsonify({
            "objects": objects,
            "count": len(objects),
            "result": "/result.jpg"
        })

    except Exception as e:

        print("PROCESS ERROR:")
        print(e)

        return jsonify({
            "error": str(e)
        }), 500


# FANUC
@app.route('/send_fanuc', methods=['POST'])
def send_fanuc_route():

    global latest_objects

    if not latest_objects:
        return jsonify({"error": "no data"}), 400

    ok = send_to_fanuc(latest_objects)

    return jsonify({
        "sent": ok,
        "count": len(latest_objects)
    })

# RESULT IMAGE
@app.route('/result.jpg')
def result_image():

    if not os.path.exists(RESULT_PATH):
        return jsonify({"error": "result not found"}), 404

    return send_file(RESULT_PATH, mimetype='image/jpeg')

# HEALTH CHECK
@app.route('/ping')
def ping():
    return "OK"

# RUN
if __name__ == '__main__':

    os.makedirs("uploads", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    print("PC SERVER STARTED ON http://0.0.0.0:5000")

    app.run(host="0.0.0.0", port=5000, debug=False)