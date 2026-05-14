from flask import Flask, render_template, request, jsonify, Response, send_file
import requests
import cv2
import os

from camera import Camera
from config_manager import load_config, save_config, is_config_ready

app = Flask(__name__)

camera = Camera(mode="raspberry")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CAPTURE_DIR = os.path.join(BASE_DIR, "captured")
STATIC_DIR = os.path.join(BASE_DIR, "static")

last_image = os.path.join(CAPTURE_DIR, "last.jpg")
result_image = os.path.join(STATIC_DIR, "result.jpg")

latest_objects = []

# START PAGE (SETUP FIRST)
@app.route('/')
def index():
    return render_template("setup.html")


# SAVE CONFIG
@app.route('/save_config', methods=['POST'])
def save_cfg():
    data = request.json
    save_config(data)

    return jsonify({
        "status": "ok",
        "redirect": "/main"
    })

# TO MAIN PAGE
@app.route('/main')
def main():
    return render_template("index.html")

# VIDEO STREAM
def gen_frames():
    while True:
        frame = camera.read_frame()
        if frame is None:
            continue

        _, buffer = cv2.imencode('.jpg', frame)

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               buffer.tobytes() + b'\r\n')


@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# CAPTURE
@app.route('/capture')
def capture():
    camera.capture(last_image)

    if not os.path.exists(last_image):
        return jsonify({"error": "no image saved"}), 500

    return jsonify({
        "status": "captured",
        "file": "/captured/last.jpg"
    })

# SAFE PC SERVER GETTER
def get_pc_server():
    cfg = load_config()

    pc = cfg.get("pc_server", "")

    if not pc:
        return None

    if not pc.startswith("http://") and not pc.startswith("https://"):
        pc = "http://" + pc

    return pc

# PROCESS IMAGE
@app.route('/process')
def process():

    global latest_objects

    PC_SERVER = get_pc_server()

    if PC_SERVER is None:
        return jsonify({"error": "PC_SERVER not set"}), 400

    if not os.path.exists(last_image):
        return jsonify({"error": "no image file exists"}), 500

    if os.path.getsize(last_image) == 0:
        return jsonify({"error": "image is empty (0 bytes)"}), 500

    with open(last_image, "rb") as f:
        files = {
            "image": ("image.jpg", f, "image/jpeg")
        }

        r = requests.post(f"{PC_SERVER}/process", files=files, timeout=10)

    print("PC STATUS:", r.status_code)
    print("PC TEXT:", r.text[:200])

    if r.status_code != 200:
        return jsonify({"error": "PC error", "status": r.status_code}), 500

    data = r.json()

    latest_objects = data.get("objects", [])

    try:
        img = requests.get(f"{PC_SERVER}/result.jpg", timeout=10).content
        with open(result_image, "wb") as f:
            f.write(img)
    except Exception as e:
        print("RESULT IMAGE ERROR:", e)

    return jsonify({
        "count": len(latest_objects),
        "objects": latest_objects,
        "result": "/static/result.jpg"
    })

# SEND TO FANUC (з разбері дописати тут за необхідності)
@app.route('/send_fanuc')
def send():
    return jsonify({
        "error": "Raspberry does not send to FANUC anymore (PC handles it)"
    })

# UPLOAD FROM PC
@app.route('/upload', methods=['POST'])
def upload():

    global latest_objects

    cfg = load_config()
    PC_SERVER = cfg.get("pc_server", "")

    print("UPLOAD PC_SERVER =", PC_SERVER)

    if not PC_SERVER:
        return jsonify({"error": "pc_server not set"}), 400

    if not PC_SERVER.startswith("http"):
        PC_SERVER = "http://" + PC_SERVER

    try:
        file = request.files.get('image')

        if file is None:
            return jsonify({"error": "no image file"}), 400

        file.save(last_image)
        print("IMAGE SAVED:", last_image)

        with open(last_image, 'rb') as f:

            files = {
                "image": ("image.jpg", f, "image/jpeg")
            }

            r = requests.post(
                f"{PC_SERVER}/process",
                files=files,
                timeout=10
            )

        print("PC RESPONSE STATUS:", r.status_code)

        data = r.json()
        latest_objects = data.get("objects", [])

        print("OBJECTS:", len(latest_objects))

        try:
            img = requests.get(f"{PC_SERVER}/result.jpg", timeout=10).content
            with open(result_image, "wb") as f:
                f.write(img)
        except Exception as e:
            print("RESULT IMAGE ERROR:", e)

        return jsonify({
            "count": len(latest_objects),
            "objects": latest_objects,
            "result": "/static/result.jpg"
        })

    except Exception as e:
        print("UPLOAD ERROR:", str(e))

        return jsonify({
            "count": 0,
            "objects": [],
            "result": "/static/result.jpg",
            "error": str(e)
        }), 500


@app.route('/captured/<filename>')
def captured_file(filename):
    return send_file(os.path.join(CAPTURE_DIR, filename))

# RUN SERVER
if __name__ == '__main__':
    os.makedirs(CAPTURE_DIR, exist_ok=True)
    os.makedirs(STATIC_DIR, exist_ok=True)

    app.run(host="0.0.0.0", port=5000, debug=False)