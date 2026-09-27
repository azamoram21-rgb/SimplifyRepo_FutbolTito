"""
Reemplazo de firmware/hw.py para el simulador: misma API publica
(set_left, set_right, set_rodillo, kick, kick_update, stop_all), pero
mueve un SimRobot/SimBall de physics.py en vez de pines reales.

robot_server.py llama estas funciones exactamente como firmware/main.py
llama a hw.py -- para el codigo que las usa no hay ninguna diferencia.
"""

import math
from physics import SimRobot, SimBall

CAPTURE_DIST = 30      # que tan cerca tiene que estar la pelota para que el rodillo la agarre
KICK_POWER = 250.0

robot = SimRobot(200, 300)
ball = SimBall(600, 300)

_duty_l = 0
_duty_r = 0
_rodillo_duty = 0
_captured = False


def set_left(duty):
    global _duty_l
    _duty_l = duty


def set_right(duty):
    global _duty_r
    _duty_r = duty


def set_rodillo(duty):
    global _rodillo_duty
    _rodillo_duty = duty


def kick():
    """Igual que hw.kick(): dispara solo si hay algo que patear (la pelota
    capturada por el rodillo, aca en vez del solenoide fisico)."""
    global _captured
    if _captured:
        ball.kick_from(robot, power=KICK_POWER)
        _captured = False
        return True
    return False


def kick_update():
    # en hw.py esto apaga el solenoide despues de KICK_MS; en la
    # simulacion el golpe es instantaneo, no hay nada que actualizar.
    pass


def stop_all():
    global _duty_l, _duty_r, _rodillo_duty
    _duty_l = 0
    _duty_r = 0
    _rodillo_duty = 0


def step(dt, bounds):
    """Llamado por run_simulator.py en cada tick de fisica: avanza el
    robot segun los ultimos duty recibidos y resuelve si el rodillo
    capturo la pelota."""
    global _captured
    robot.step(_duty_l, _duty_r, dt)

    d = math.hypot(ball.x - robot.x, ball.y - robot.y)
    if _rodillo_duty > 0 and d < CAPTURE_DIST:
        _captured = True
    if _captured and _rodillo_duty == 0:
        _captured = False

    if _captured:
        rad = math.radians(robot.theta)
        ball.x = robot.x + 20 * math.cos(rad)
        ball.y = robot.y + 20 * math.sin(rad)
        ball.vx = ball.vy = 0.0
    else:
        ball.step(dt, bounds)
