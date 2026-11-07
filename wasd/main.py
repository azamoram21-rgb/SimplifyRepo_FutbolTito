"""
Control manual por teclado + video de la camara (Raspberry Pi).

Requiere estar conectado a la red WiFi del robot (ver firmware/main.py).
La camara va montada en el robot (vista en primera persona). El PC NO
procesa imagen: la Pi (camera_server.py) detecta la pelota, dibuja sobre el
video y lo transmite; aqui solo se muestra.

Usa pygame en vez de la libreria `keyboard` a proposito: `keyboard` pide
permisos de root en Linux y de Accesibilidad en macOS; pygame no.

WASD: avanzar/girar. SPACE: patea. SHIFT: rodillo. ESC: salir.
"""

import io
import sys
import pygame

from client import RobotLink
from video_client import VideoStream

DUTY = 35          # velocidad al avanzar/retroceder (antes 60)
TURN_DUTY = 25     # velocidad extra por rueda al girar
HZ = 20

RAMP = 6           # cambio maximo de duty por ciclo (a 20 Hz: 0->35 en ~0.3 s)

# Compensacion para que avance recto. Baja la rueda que va mas rapida.
# Si se ladea a la derecha, la izquierda es la rapida: baja TRIM_L.
# Si se ladea a la izquierda, baja TRIM_R. Ajustar de a 0.03-0.05.
TRIM_L = 1.00
TRIM_R = 1.00

VIDEO_W, VIDEO_H = 640, 480    # tamano en pantalla; el video de la Pi (320x240) se escala a esto
HUD_H = 70
VIDEO_STALE_S = 1.0            # sin frames por mas de esto -> se avisa en rojo


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
    screen = pygame.display.set_mode((VIDEO_W, VIDEO_H + HUD_H))
    pygame.display.set_caption("IRB1010 - control manual + camara")
    font = pygame.font.SysFont(None, 22)
    big_font = pygame.font.SysFont(None, 40)
    clock = pygame.time.Clock()

    link = RobotLink()
    video = VideoStream()

    vl = vr = 0            # velocidad actual (con rampa)
    frame_surf = None
    last_seq = -1

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

        # --- video: decodificar solo si llego un frame nuevo ---
        seq, jpeg = video.latest()
        if jpeg is not None and seq != last_seq:
            try:
                surf = pygame.image.load(io.BytesIO(jpeg), "frame.jpg").convert()
                if surf.get_size() != (VIDEO_W, VIDEO_H):
                    surf = pygame.transform.scale(surf, (VIDEO_W, VIDEO_H))
                frame_surf = surf
                last_seq = seq
            except pygame.error:
                pass   # frame corrupto: se mantiene el anterior

        screen.fill((30, 30, 30))
        stale = video.age() > VIDEO_STALE_S
        if frame_surf is not None:
            screen.blit(frame_surf, (0, 0))
        if frame_surf is None or stale:
            # Un frame congelado parece video en vivo: avisar siempre que no lo sea.
            motivo = video.error or "esperando frames..."
            msg = big_font.render("SIN VIDEO", True, (255, 60, 60))
            sub = font.render(motivo, True, (255, 200, 0))
            screen.blit(msg, (10, 10))
            screen.blit(sub, (10, 50))

        y0 = VIDEO_H + 8
        help_txt = font.render("WASD mover, SPACE patea, SHIFT rodillo, ESC salir", True, (200, 200, 200))
        screen.blit(help_txt, (10, y0))
        state_txt = font.render(f"vl={vl}  vr={vr}  sol={sol}  rod={rod}", True, (255, 255, 255))
        screen.blit(state_txt, (10, y0 + 22))
        vid_txt = font.render("video: OK" if not stale else "video: SIN SENAL", True,
                              (120, 255, 120) if not stale else (255, 60, 60))
        screen.blit(vid_txt, (10, y0 + 44))
        pygame.display.flip()

        clock.tick(HZ)

    video.close()
    link.close()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()