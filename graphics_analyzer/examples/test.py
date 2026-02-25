import threading
import time

shared_state = {"x": 0}
lock = threading.Lock()

def user_script():
    while True:
        with lock:
            shared_state["x"] += 1
        time.sleep(0.1)

def engine_loop():
    while True:
        with lock:
            x = shared_state["x"]
        print("Render frame, x =", x)
        time.sleep(0.016)  # ~60 FPS

threading.Thread(target=user_script, daemon=True).start()
engine_loop()
