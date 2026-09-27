"""
El "mundo" del simulador: fisica del robot y la pelota, arma la camara
falsa en memoria compartida, y levanta el servidor TCP que recibe
"vl,vr,sol,rod" -- exactamente como haria el Pico real.

Correr esto en una terminal, y en OTRA:
    cd autonomous && python main_sim.py

La ventana que abre este archivo es una vista "de afuera": util para
depurar el simulador mismo (con marcador de goles), pero NO es lo que "ve"
el robot -- eso se ve solo en la ventana de main_sim.py, que recibe unicamente
la camara falsa (memoria compartida), igual que pasaria con hardware real.

Teclas en esta ventana: r reinicia posiciones, q / ESC sale.
"""

import time
from multiprocessing import shared_memory

import cv2
import numpy as np

import hw_sim
import camera_sim
import robot_server
from camera_sim import WIDTH, HEIGHT, CHANNELS

FPS = 60
GOAL_HALF_HEIGHT = camera_sim.GOAL_HALF_HEIGHT
SHM_NAME = "irb1010_sim_cam"


def _make_shared_memory():
    size = HEIGHT * WIDTH * CHANNELS
    try:
        old = shared_memory.SharedMemory(name=SHM_NAME)
        old.close()
        old.unlink()
    except FileNotFoundError:
        pass
    return shared_memory.SharedMemory(create=True, name=SHM_NAME, size=size)


def reset_positions():
    hw_sim.robot.x, hw_sim.robot.y, hw_sim.robot.theta = WIDTH / 4, HEIGHT / 2, 0.0
    hw_sim.ball.x, hw_sim.ball.y = WIDTH * 3 / 4, HEIGHT / 2
    hw_sim.ball.vx = hw_sim.ball.vy = 0.0


def check_goal():
    """Devuelve 'own', 'opp' o None si la pelota entro a algun arco."""
    b = hw_sim.ball
    cy = HEIGHT / 2
    if abs(b.y - cy) > GOAL_HALF_HEIGHT:
        return None
    if b.x <= 0:
        return "own"    # le metieron gol al robot
    if b.x >= WIDTH:
        return "opp"    # el robot metio gol
    return None


def main():
    shm = _make_shared_memory()
    shm_frame = np.ndarray((HEIGHT, WIDTH, CHANNELS), dtype=np.uint8, buffer=shm.buf)

    reset_positions()
    robot_server.start_server_thread()

    score = {"own": 0, "opp": 0}
    last_t = time.time()

    print("Simulador corriendo. Conecta autonomous/main_sim.py en otra terminal.")

    try:
        while True:
            now = time.time()
            dt = now - last_t
            last_t = now

            hw_sim.step(dt, (WIDTH, HEIGHT))

            gol = check_goal()
            if gol is not None:
                score[gol] += 1
                print(f"GOL -- marcador: propio {score['own']} / rival {score['opp']}")
                reset_positions()

            frame = camera_sim.render(hw_sim.robot, hw_sim.ball)
            shm_frame[:] = frame   # esto es exactamente lo que "ve" main_sim.py

            debug = frame.copy()
            cv2.putText(
                debug,
                f"[vista externa, no es la camara]  propio {score['own']} - rival {score['opp']}",
                (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2,
            )
            cv2.imshow("IRB1010 - simulador (vista externa)", debug)

            key = cv2.waitKey(max(1, int(1000 / FPS))) & 0xFF
            if key in (ord("q"), 27):
                break
            elif key == ord("r"):
                reset_positions()

    finally:
        cv2.destroyAllWindows()
        shm.close()
        shm.unlink()


if __name__ == "__main__":
    main()
