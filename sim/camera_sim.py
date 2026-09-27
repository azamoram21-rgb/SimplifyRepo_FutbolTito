"""
Dibuja la cancha (arcos + pelota + marcador ArUco del robot) para la
"camara falsa" del simulador. Solo dibuja: la fisica vive en physics.py y
hw_sim.py, la memoria compartida y el servidor en run_simulator.py.
"""

import cv2
import numpy as np

import aruco_render

WIDTH, HEIGHT, CHANNELS = 800, 600, 3

FIELD_GREEN = (0, 130, 0)
LINE_WHITE = (255, 255, 255)
BALL_COLOR_BGR = (0, 150, 255)   # cae dentro de autonomous/vision.BALL_HSV_LOW/HIGH
GOAL_COLOR = (255, 255, 255)

GOAL_HALF_HEIGHT = int(HEIGHT * 0.18)


def render(robot, ball, robot_marker_id=0):
    """Devuelve un frame BGR (numpy) con la cancha, la pelota y el
    marcador ArUco del robot en su posicion/angulo actuales."""
    frame = np.full((HEIGHT, WIDTH, CHANNELS), FIELD_GREEN, dtype=np.uint8)
    cv2.rectangle(frame, (0, 0), (WIDTH - 1, HEIGHT - 1), LINE_WHITE, 3)
    cv2.line(frame, (WIDTH // 2, 0), (WIDTH // 2, HEIGHT), LINE_WHITE, 1)

    cy = HEIGHT // 2
    cv2.line(frame, (0, cy - GOAL_HALF_HEIGHT), (0, cy + GOAL_HALF_HEIGHT), GOAL_COLOR, 6)
    cv2.line(frame, (WIDTH - 1, cy - GOAL_HALF_HEIGHT), (WIDTH - 1, cy + GOAL_HALF_HEIGHT), GOAL_COLOR, 6)

    cv2.circle(frame, (int(ball.x), int(ball.y)), 10, BALL_COLOR_BGR, -1)

    aruco_render.draw_robot_marker(frame, robot_marker_id, robot.x, robot.y, robot.theta)

    return frame
