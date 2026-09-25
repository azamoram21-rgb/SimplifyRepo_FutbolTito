"""
Rutinas de demostracion. Cada funcion toma el estado actual (robot, pelota,
etc) y devuelve (vl, vr, sol, rod) para enviar al robot via client.RobotLink.
Control P simple: primero gira hacia el objetivo, avanza cuando ya esta
alineado.
"""

import math

MAX_DUTY = 70
ANGLE_TOL_DEG = 10
STOP_DIST_PX = 25


def _clip(v, lo=-MAX_DUTY, hi=MAX_DUTY):
    return max(lo, min(hi, v))


def to_target(robot, target_xy, k_ang=1.2, k_lin=0.3, max_duty=MAX_DUTY):
    if robot.pos == (-1, -1) or target_xy is None:
        return 0, 0

    dx = target_xy[0] - robot.pos[0]
    dy = target_xy[1] - robot.pos[1]
    distancia = math.hypot(dx, dy)

    if distancia < STOP_DIST_PX:
        return 0, 0

    angulo_objetivo = math.degrees(math.atan2(dy, dx))
    error_ang = angulo_objetivo - robot.angle
    error_ang = (error_ang + 180) % 360 - 180   # normalizar a [-180, 180]

    giro = _clip(k_ang * error_ang, -max_duty, max_duty)

    avance = 0
    if abs(error_ang) < ANGLE_TOL_DEG:
        avance = _clip(k_lin * distancia, 0, max_duty)

    vl = _clip(avance - giro, -max_duty, max_duty)
    vr = _clip(avance + giro, -max_duty, max_duty)
    return int(vl), int(vr)


def go_to_center(robot, frame_shape):
    """Modo 2: ir al centro de la cancha."""
    centro = (frame_shape[1] / 2, frame_shape[0] / 2)
    vl, vr = to_target(robot, centro)
    return vl, vr, 0, 0


def chase_ball(robot, ball):
    """Modo 3: perseguir la pelota, prender el rodillo al llegar."""
    if ball.pos == (-1, -1):
        return 0, 0, 0, 0
    vl, vr = to_target(robot, ball.pos)
    cerca = math.hypot(ball.pos[0] - robot.pos[0], ball.pos[1] - robot.pos[1]) < STOP_DIST_PX * 1.5
    rod = 60 if cerca else 0
    return vl, vr, 0, rod


def dribble_to_center(robot, ball, frame_shape):
    """Modo 4: perseguir la pelota; al tenerla, rodillo + llevarla al centro."""
    if ball.pos == (-1, -1):
        return 0, 0, 0, 0

    d_robot_pelota = math.hypot(ball.pos[0] - robot.pos[0], ball.pos[1] - robot.pos[1])
    tiene_pelota = d_robot_pelota < STOP_DIST_PX * 1.5

    if not tiene_pelota:
        vl, vr = to_target(robot, ball.pos)
        return vl, vr, 0, 0

    centro = (frame_shape[1] / 2, frame_shape[0] / 2)
    vl, vr = to_target(robot, centro, k_lin=0.25)
    return vl, vr, 0, 70
