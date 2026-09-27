"""
Genera y ubica el marcador ArUco del robot simulado sobre el frame de la
camara falsa, para que autonomous/vision.py lo detecte con el mismo
detector (cv2.aruco.ArucoDetector) que usaria en la cancha real.
"""

import cv2
import numpy as np

DICT_NAME = cv2.aruco.DICT_4X4_1000
MARKER_PX = 60   # tamano del marcador dibujado, en pixeles de la "camara"

_aruco_dict = cv2.aruco.getPredefinedDictionary(DICT_NAME)
_marker_cache = {}


def _get_marker_image(marker_id):
    if marker_id not in _marker_cache:
        img = cv2.aruco.generateImageMarker(_aruco_dict, marker_id, MARKER_PX)
        _marker_cache[marker_id] = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    return _marker_cache[marker_id]


def draw_robot_marker(frame, marker_id, x, y, angle_deg):
    """Pega el marcador `marker_id`, rotado a `angle_deg`, centrado en (x, y).

    Si el angulo que detecta vision.py sale invertido respecto al que le
    pasas aca, es cuestion de signo en la rotacion: ajustar el signo de
    angle_deg mas abajo (no afecta a nada mas del simulador).
    """
    marker = _get_marker_image(marker_id)
    size = marker.shape[0]
    center = (size / 2, size / 2)

    rot_mat = cv2.getRotationMatrix2D(center, -angle_deg, 1.0)
    rotated = cv2.warpAffine(
        marker, rot_mat, (size, size), borderValue=(255, 255, 255)
    )

    x0, y0 = int(x - size / 2), int(y - size / 2)
    x1, y1 = x0 + size, y0 + size

    fh, fw = frame.shape[:2]
    if x0 < 0 or y0 < 0 or x1 > fw or y1 > fh:
        return   # fuera de cuadro, no se dibuja (igual que pasaria con la camara real)

    frame[y0:y1, x0:x1] = rotated
