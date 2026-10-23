"""
Demo IRB1010: camara + ArUco + pelota -> comportamiento -> robot.

Antes de correr: conectar el WiFi del PC a la red del robot (ver
firmware/main.py, SSID/clave por defecto "FutBot_1" / "futbot123").

Modos (teclas, con la ventana de video en foco):
  1  IDLE (motores detenidos)
  2  Ir al centro de la cancha
  3  Perseguir la pelota
  4  Llevar la pelota al centro (dribbling)
  q  Salir (detiene el robot)
"""

import cv2

from vision import FieldTracker
from client import RobotLink
import behaviors

ROBOT_ARUCO_ID = 0   # id del marcador del robot que se esta controlando


def main():
    tracker = FieldTracker(cam_index=0)
    link = RobotLink()
    mode = "1"

    try:
        while True:
            frame = tracker.read()
            if frame is None:
                continue

            robot = tracker.robots.get(ROBOT_ARUCO_ID)
            vl = vr = sol = rod = 0

            if robot is not None:
                if mode == "2":
                    vl, vr, sol, rod = behaviors.go_to_center(robot, frame.shape)
                elif mode == "3":
                    vl, vr, sol, rod = behaviors.chase_ball(robot, tracker.ball)
                elif mode == "4":
                    vl, vr, sol, rod = behaviors.dribble_to_center(robot, tracker.ball, frame.shape)

            link.send(vl, vr, sol, rod)

            tracker.draw(frame)
            cv2.putText(
                frame, f"MODO: {mode}  vl={vl} vr={vr} rod={rod}",
                (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2,
            )
            cv2.imshow("IRB1010 - demo", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key in (ord("1"), ord("2"), ord("3"), ord("4")):
                mode = chr(key)

    finally:
        link.close()
        tracker.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
