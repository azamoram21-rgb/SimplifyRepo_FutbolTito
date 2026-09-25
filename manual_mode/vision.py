"""
Deteccion de robots (ArUco) y pelota (color) para el demo del IRB1010.
Unico archivo que toca OpenCV/ArUco.
"""

import math
import cv2
import numpy as np

ArucoType = {
    "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
    "DICT_4X4_100": cv2.aruco.DICT_4X4_100,
    "DICT_4X4_250": cv2.aruco.DICT_4X4_250,
    "DICT_4X4_1000": cv2.aruco.DICT_4X4_1000,
}

# HSV de la pelota. Ajustar con el color real (probar en la cancha).
BALL_HSV_LOW = (15, 50, 50)
BALL_HSV_HIGH = (30, 255, 255)
BALL_MIN_AREA = 200


def dist(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


class Robot:
    """Pose de un robot detectado por su marcador ArUco."""

    def __init__(self, marker_id):
        self.id = marker_id
        self.pos = (-1, -1)
        self.angle = 0.0
        self.corners = None

    def update(self, corners):
        tl, tr, br, bl = corners
        top_c = ((tl[0] + tr[0]) / 2, (tl[1] + tr[1]) / 2)
        bot_c = ((bl[0] + br[0]) / 2, (bl[1] + br[1]) / 2)
        self.pos = (int((top_c[0] + bot_c[0]) / 2), int((top_c[1] + bot_c[1]) / 2))
        self.top_centre = (int(top_c[0]), int(top_c[1]))
        dx = self.top_centre[0] - self.pos[0]
        dy = self.top_centre[1] - self.pos[1]
        self.angle = math.degrees(math.atan2(dy, dx))
        self.corners = corners

    def draw(self, frame, color=(255, 0, 0)):
        if self.corners is None:
            return
        pts = np.array(self.corners, dtype=np.int32)
        cv2.polylines(frame, [pts], True, color, 2)
        cv2.line(frame, self.pos, self.top_centre, color, 2)
        cv2.putText(
            frame, f"ID {self.id} {int(self.angle)}deg",
            (int(self.corners[0][0]), int(self.corners[0][1]) - 8),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2,
        )


class Ball:
    def __init__(self):
        self.pos = (-1, -1)
        self.box = None

    def update(self, box):
        if box is None:
            return
        x, y, w, h = box
        self.pos = (int(x + w / 2), int(y + h / 2))
        self.box = box

    def draw(self, frame, color=(0, 255, 0)):
        if self.box is None:
            return
        x, y, w, h = self.box
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        cv2.circle(frame, self.pos, 5, color, -1)


def _detect_ball_box(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, BALL_HSV_LOW, BALL_HSV_HIGH)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = [c for c in contours if cv2.contourArea(c) > BALL_MIN_AREA]
    if not contours:
        return None
    largest = max(contours, key=cv2.contourArea)   # antes se tomaba el primer contorno, no el mas grande
    return cv2.boundingRect(largest)


class FieldTracker:
    """Envuelve la camara + deteccion de ArUco y pelota."""

    def __init__(self, cam_index=0, dict_name="DICT_4X4_1000"):
        self.cap = cv2.VideoCapture(cam_index)
        if not self.cap.isOpened():
            raise RuntimeError(f"No se pudo abrir la camara (indice {cam_index}).")
        aruco_dict = cv2.aruco.getPredefinedDictionary(ArucoType[dict_name])
        params = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(aruco_dict, params)
        self.robots = {}   # id -> Robot
        self.ball = Ball()

    def read(self):
        ret, frame = self.cap.read()
        if not ret or frame is None:
            return None

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = self.detector.detectMarkers(gray)
        if ids is not None:
            for i, marker_id in enumerate(ids.flatten()):
                mid = int(marker_id)
                if mid not in self.robots:
                    self.robots[mid] = Robot(mid)
                self.robots[mid].update(corners[i][0])

        box = _detect_ball_box(frame)
        if box is not None:
            self.ball.update(box)

        return frame

    def draw(self, frame):
        for r in self.robots.values():
            r.draw(frame)
        self.ball.draw(frame)

    def release(self):
        self.cap.release()
