import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config_json")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}

    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save_config(data):

    os.makedirs(CONFIG_DIR, exist_ok=True)

    ip = data.get("pc_ip", "").strip()
    port = data.get("pc_port", "").strip()
    
    if ip and port:
        data["pc_server"] = f"http://{ip}:{port}"

    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)


def is_config_ready():
    cfg = load_config()
    return bool(cfg.get("pc_server"))