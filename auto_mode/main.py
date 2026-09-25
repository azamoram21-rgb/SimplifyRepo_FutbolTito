"""
Control manual por teclado. Requiere estar conectado a la red WiFi del
robot (ver firmware/main.py). No usa camara ni ArUco.

Usa pygame en vez de la libreria `keyboard` a proposito: `keyboard` pide
permisos de root en Linux y de Accesibilidad en macOS; pygame no.

WASD: avanzar/girar. SPACE: patea. SHIFT: rodillo. ESC: salir.
"""

import sys
import pygame

from client import RobotLink

DUTY = 60
TURN_DUTY = DUTY // 2
HZ = 20


def compute_command(keys):
    vl = vr = 0

    # Chequeos independientes (no elif encadenado): W+D hace una curva
    # en vez de solo avanzar o solo girar.
    if keys[pygame.K_w]:
        vl += DUTY
        vr += DUTY
    if keys[pygame.K_s]:
        vl -= DUTY
        vr -= DUTY
    if keys[pygame.K_a]:
        vl -= TURN_DUTY
        vr += TURN_DUTY
    if keys[pygame.K_d]:
        vl += TURN_DUTY
        vr -= TURN_DUTY

    vl = max(-100, min(100, vl))
    vr = max(-100, min(100, vr))

    sol = 1 if keys[pygame.K_SPACE] else 0
    rod = 80 if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) else 0
    return vl, vr, sol, rod


def main():
    pygame.init()
    screen = pygame.display.set_mode((320, 120))
    pygame.display.set_caption("IRB1010 - control manual")
    font = pygame.font.SysFont(None, 22)
    clock = pygame.time.Clock()

    link = RobotLink()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        keys = pygame.key.get_pressed()
        vl, vr, sol, rod = compute_command(keys)
        link.send(vl, vr, sol, rod)

        screen.fill((30, 30, 30))
        help_txt = font.render("WASD mover, SPACE patea, SHIFT rodillo, ESC salir", True, (200, 200, 200))
        screen.blit(help_txt, (10, 10))
        state_txt = font.render(f"vl={vl}  vr={vr}  sol={sol}  rod={rod}", True, (255, 255, 255))
        screen.blit(state_txt, (10, 45))
        pygame.display.flip()

        clock.tick(HZ)

    link.close()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
