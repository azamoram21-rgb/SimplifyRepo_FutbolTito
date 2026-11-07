"""
Servidor de camara para la Raspberry Pi 4 + Camera Module 2, montada EN el
robot y mirando hacia adelante (vista en primera persona).

Todo el procesamiento de imagen ocurre aqui (deteccion de la pelota). El PC
solo recibe el video ya anotado y lo muestra; no necesita OpenCV. No se usa
ArUco: con la camara a bordo el robot no puede verse a si mismo.

Instalar en la Pi (Raspberry Pi OS Bookworm). Hacerlo ANTES de conectarla a
la red del robot, porque esa red no tiene internet:
    sudo apt install -y python3-picamera2 python3-opencv python3-numpy

Correr con el python del sistema (no en un venv aislado):
    python3 camera_server.py

Endpoints (puerto 8000):
    /stream      video MJPEG con la pelota marcada
    /state.json  posicion de la pelota en la imagen (para rutinas futuras /
                 nodo ROS2; el modo WASD no lo necesita)
"""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2
import numpy as np

HOST = "0.0.0.0"
PORT = 8000

# Resolucion/fps/calidad bajos A PROPOSITO: el video y los comandos del robot
# comparten el mismo WiFi (el del Pico). Subir de a poco mientras se verifica
# que el robot sigue respondiendo bien (el watchdog lo frena a los 500 ms).
WIDTH, HEIGHT = 320, 240
FPS = 15
JPEG_QUALITY = 60
FLIP = False             # True si la camara esta montada al reves (gira 180 grados)

DETECT_BALL = True       # False = solo transmitir video, sin procesar nada

# HSV de la pelota. Ajustar con el color real y la luz de la cancha.
BALL_HSV_LOW = np.array([15, 50, 50], dtype=np.uint8)
BALL_HSV_HIGH = np.array([30, 255, 255], dtype=np.uint8)
BALL_MIN_AREA = 50       # en px^2 a 320x240 (equivale a 200 a 640x480)

FONT = cv2.FONT_HERSHEY_SIMPLEX


def find_ball(frame):
    """Devuelve el bounding box (x, y, w, h) del contorno mas grande, o None."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, BALL_HSV_LOW, BALL_HSV_HIGH)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = [c for c in contours if cv2.contourArea(c) > BALL_MIN_AREA]
    if not contours:
        return None
    return cv2.boundingRect(max(contours, key=cv2.contourArea))


def process_frame(frame, fps=0.0):
    """Dibuja sobre `frame` (BGR) y devuelve (frame, estado).

    estado["ball"] es None o {"pos": [x, y] en px, "nx": -1..1, "width": px}
    donde nx = -1 es el borde izquierdo de la imagen, 0 el centro y +1 el
    derecho. width (ancho de la pelota en px) crece al acercarse: sirve como
    estimacion de distancia.
    """
    h_img, w_img = frame.shape[:2]

    ball = None
    box = find_ball(frame) if DETECT_BALL else None
    if box is not None:
        x, y, w, h = box
        cx, cy = x + w / 2, y + h / 2
        ball = {
            "pos": [int(cx), int(cy)],
            "nx": round((cx - w_img / 2) / (w_img / 2), 3),
            "width": int(w),
        }
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.circle(frame, (int(cx), int(cy)), 3, (0, 255, 0), -1)
        cv2.putText(frame, "Ball", (x, max(12, y - 6)), FONT, 0.45, (0, 255, 0), 1)

    cv2.putText(frame, "Pi {:.0f} fps".format(fps), (6, h_img - 8), FONT, 0.4, (255, 255, 255), 1)

    state = {"t": time.time(), "frame": [w_img, h_img], "ball": ball}
    return frame, state


class Shared:
    """Ultimo frame JPEG + estado, compartido entre la captura y los clientes HTTP."""

    def __init__(self):
        self._cond = threading.Condition()
        self._jpeg = None
        self._state = {"t": 0, "frame": [WIDTH, HEIGHT], "ball": None}
        self._seq = 0

    def publish(self, jpeg, state):
        with self._cond:
            self._jpeg = jpeg
            self._state = state
            self._seq += 1
            self._cond.notify_all()

    def wait_frame(self, last_seq, timeout=2.0):
        with self._cond:
            self._cond.wait_for(lambda: self._seq != last_seq, timeout)
            return self._seq, self._jpeg

    def state(self):
        with self._cond:
            return self._state


def make_handler(shared):
    class Handler(BaseHTTPRequestHandler):
        timeout = 5   # si un cliente deja de leer, la escritura falla en vez de colgarse

        def log_message(self, *args):
            pass

        def do_GET(self):
            if self.path == "/stream":
                self._stream()
            elif self.path == "/state.json":
                body = json.dumps(shared.state()).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_error(404)

        def _stream(self):
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            seq = -1
            try:
                while True:
                    new_seq, jpeg = shared.wait_frame(seq)
                    if jpeg is None or new_seq == seq:
                        continue
                    seq = new_seq
                    self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: "
                                     + str(len(jpeg)).encode() + b"\r\n\r\n")
                    self.wfile.write(jpeg)
                    self.wfile.write(b"\r\n")
            except OSError:
                pass   # el cliente se desconecto

    return Handler


def capture_loop(shared):
    from picamera2 import Picamera2   # import aqui para poder probar el resto sin camara

    cam = Picamera2()
    cfg = cam.create_video_configuration(
        main={"size": (WIDTH, HEIGHT), "format": "RGB888"},   # en memoria queda en orden BGR (lo que usa OpenCV)
        controls={"FrameRate": FPS},
    )
    cam.configure(cfg)
    cam.start()

    fps = 0.0
    t_prev = time.monotonic()
    try:
        while True:
            frame = cam.capture_array("main")
            if FLIP:
                frame = cv2.rotate(frame, cv2.ROTATE_180)

            now = time.monotonic()
            dt = now - t_prev
            t_prev = now
            if dt > 0:
                fps = 0.9 * fps + 0.1 * (1.0 / dt)

            frame, state = process_frame(frame, fps)
            ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
            if ok:
                shared.publish(buf.tobytes(), state)
    finally:
        cam.stop()


def main():
    shared = Shared()
    server = ThreadingHTTPServer((HOST, PORT), make_handler(shared))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print("Camara lista. Video en http://<ip-de-la-pi>:{}/stream  (Ctrl+C para salir)".format(PORT))
    try:
        capture_loop(shared)   # en el hilo principal: si la camara falla, el programa termina con el error
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()