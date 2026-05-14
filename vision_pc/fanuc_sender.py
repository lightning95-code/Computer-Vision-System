import socket
import json
from config_manager import load_config

def send_to_fanuc(data):

    cfg = load_config()

    HOST = cfg.get("fanuc_ip")
    PORT = int(cfg.get("fanuc_port", 5000))

    try:
        s = socket.socket()
        s.connect((HOST, PORT))
        s.send(json.dumps(data).encode())
        s.close()
        return True

    except Exception as e:
        print("FANUC error:", e)
        return False