"""
Control manual por teclado, SIN camara. Requiere estar conectado a la red
WiFi del robot (ver firmware/main.py). Solo necesita client.py y pygame.

Para la version con video de la Raspberry Pi, usar main.py.

Usa pygame en vez de la libreria `keyboard` a proposito: `keyboard` pide
permisos de root en Linux y de Accesibilidad en macOS; pygame no.

WASD: avanzar/girar. SPACE: patea. SHIFT: rodillo. ESC: salir.
"""

import sys
import pygame

from client import RobotLink

DUTY = 35          # velocidad al avanzar/retroceder (antes 60)
TURN_DUTY = 25     # velocidad extra por rueda al girar
HZ = 20

RAMP = 6           # cambio maximo de duty por ciclo (a 20 Hz: 0->35 en ~0.3 s)

# Compensacion para que avance recto. Baja la rueda que va mas rapida.
# Si se ladea a la derecha, la izquierda es la rapida: baja TRIM_L.
# Si se ladea a la izquierda, baja TRIM_R. Ajustar de a 0.03-0.05.
TRIM_L = 1.00
TRIM_R = 1.00


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

    vl = int(vl * TRIM_L)
    vr = int(vr * TRIM_R)

    sol = 1 if keys[pygame.K_SPACE] else 0
    rod = 80 if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) else 0
    return vl, vr, sol, rod


def ramp(actual, objetivo, paso=RAMP):
    """Acerca `actual` a `objetivo` de a `paso`. Frenar es inmediato."""
    if objetivo == 0:
        return 0
    if objetivo > actual:
        return min(objetivo, actual + paso)
    return max(objetivo, actual - paso)


def main():
    pygame.init()
    screen = pygame.display.set_mode((320, 120))
    pygame.display.set_caption("IRB1010 - control manual")
    font = pygame.font.SysFont(None, 22)
    clock = pygame.time.Clock()

    link = RobotLink()

    vl = vr = 0   # velocidad actual (con rampa)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        keys = pygame.key.get_pressed()
        vl_obj, vr_obj, sol, rod = compute_command(keys)
        vl = ramp(vl, vl_obj)
        vr = ramp(vr, vr_obj)
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