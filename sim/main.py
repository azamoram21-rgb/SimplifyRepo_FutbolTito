"""
Simulador sin hardware: corre las mismas rutinas de demo (behaviors.py)
sobre un robot y una pelota simulados en pygame. Sirve para probar y
calibrar ganancias antes de subir nada al robot real.

Modos (teclas):
  1  IDLE
  2  Ir al centro de la cancha
  3  Perseguir la pelota
  4  Llevar la pelota al centro (dribbling)
  r  Reiniciar posiciones
  q / ESC  Salir
"""

import math
import sys
import pygame

import behaviors
from physics import SimRobot, SimBall

WIDTH, HEIGHT = 800, 600
FPS = 60
CAPTURE_DIST = 30

WHITE = (255, 255, 255)
GREEN = (0, 150, 0)
RED = (200, 0, 0)
YELLOW = (255, 220, 0)
BLACK = (0, 0, 0)


def reset(robot, ball):
    robot.x, robot.y, robot.theta = WIDTH / 4, HEIGHT / 2, 0.0
    ball.x, ball.y, ball.vx, ball.vy = WIDTH * 3 / 4, HEIGHT / 2, 0.0, 0.0


def draw(screen, robot, ball, mode):
    screen.fill(GREEN)
    pygame.draw.rect(screen, WHITE, (0, 0, WIDTH, HEIGHT), 4)

    rad = math.radians(robot.angle)
    nose = (robot.x + 18 * math.cos(rad), robot.y + 18 * math.sin(rad))
    pygame.draw.circle(screen, RED, (int(robot.x), int(robot.y)), 15)
    pygame.draw.line(screen, BLACK, (robot.x, robot.y), nose, 3)

    pygame.draw.circle(screen, YELLOW, (int(ball.x), int(ball.y)), 8)

    font = pygame.font.SysFont(None, 24)
    txt = font.render(
        f"modo {mode}  (1 idle, 2 centro, 3 perseguir, 4 dribbling, r reset, q salir)",
        True, BLACK,
    )
    screen.blit(txt, (10, 10))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("IRB1010 - simulador (sin hardware)")
    clock = pygame.time.Clock()

    robot = SimRobot(WIDTH / 4, HEIGHT / 2)
    ball = SimBall(WIDTH * 3 / 4, HEIGHT / 2)

    mode = "1"
    captured = False
    prev_sol = 0

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif event.key == pygame.K_r:
                    reset(robot, ball)
                    captured = False
                elif event.unicode in ("1", "2", "3", "4"):
                    mode = event.unicode

        # behaviors.py solo necesita .pos / .angle en robot y ball,
        # que SimRobot/SimBall ya exponen -> se usa tal cual, sin adaptar nada.
        vl = vr = sol = rod = 0
        if mode == "2":
            vl, vr, sol, rod = behaviors.go_to_center(robot, (HEIGHT, WIDTH))
        elif mode == "3":
            vl, vr, sol, rod = behaviors.chase_ball(robot, ball)
        elif mode == "4":
            vl, vr, sol, rod = behaviors.dribble_to_center(robot, ball, (HEIGHT, WIDTH))

        robot.step(vl, vr, dt)

        dist_robot_ball = math.hypot(ball.x - robot.x, ball.y - robot.y)
        if rod > 0 and dist_robot_ball < CAPTURE_DIST:
            captured = True
        if captured and rod == 0:
            captured = False

        if captured:
            rad = math.radians(robot.theta)
            ball.x = robot.x + 20 * math.cos(rad)
            ball.y = robot.y + 20 * math.sin(rad)
            ball.vx = ball.vy = 0.0
            if sol and not prev_sol:
                ball.kick_from(robot)
                captured = False
        else:
            ball.step(dt, (WIDTH, HEIGHT))
        prev_sol = sol

        draw(screen, robot, ball, mode)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
