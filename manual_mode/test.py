"""
Menu interactivo para probar cada componente por separado.

Correr con las ruedas EN EL AIRE. Requiere una consola REPL (Thonny, mpremote,
etc.) porque usa input().
"""

import time
import hw


def _prompt(msg):
    try:
        return input(msg)
    except EOFError:
        return ""


def test_motor(nombre, set_fn):
    raw = _prompt("  Duty para {} (-100 a 100, Enter=30): ".format(nombre)).strip()
    duty = int(raw) if raw else 30
    duracion = 2
    print("  {}: duty={} por {}s".format(nombre, duty, duracion))
    try:
        set_fn(duty)
        time.sleep(duracion)
    finally:
        set_fn(0)
    print("  {} detenido.".format(nombre))


def test_encoders(segundos=2):
    print("  Girando M1 y M2 a duty=30, contando flancos de ENC_A...")
    count_1 = 0
    count_2 = 0
    prev_1 = hw.d1_enc_a.value()
    prev_2 = hw.d2_enc_a.value()
    hw.set_left(30)
    hw.set_right(30)
    t_fin = time.ticks_add(time.ticks_ms(), int(segundos * 1000))
    try:
        while time.ticks_diff(t_fin, time.ticks_ms()) > 0:
            v1 = hw.d1_enc_a.value()
            v2 = hw.d2_enc_a.value()
            if v1 and not prev_1:
                count_1 += 1
            if v2 and not prev_2:
                count_2 += 1
            prev_1, prev_2 = v1, v2
    finally:
        hw.stop_all()
    print("  Pulsos en {}s -> M1: {}, M2: {}".format(segundos, count_1, count_2))


def test_kick():
    print("  Disparando solenoide...")
    hw.kick()
    t_fin = time.ticks_add(time.ticks_ms(), 1000)
    while time.ticks_diff(t_fin, time.ticks_ms()) > 0:
        hw.kick_update()
    print("  Listo. Si se dispara de nuevo antes de ~500ms no pasa nada (cooldown).")


def test_leds():
    for led in (hw.led, hw.led_verde, hw.led_amarillo, hw.led_azul):
        led.on()
        time.sleep(0.3)
        led.off()
    print("  LEDs probados (onboard, verde, amarillo, azul en orden).")


MENU = """
==== Test de componentes IRB1010 (ruedas en el aire) ====
1) Motor izquierdo (M1)
2) Motor derecho (M2)
3) Rodillo
4) Encoders (gira M1 y M2 juntos, cuenta pulsos)
5) Solenoide (kick)
6) LEDs
0) Salir
"""


def main():
    hw.stop_all()
    while True:
        print(MENU)
        opt = _prompt("Opcion: ").strip()
        if opt == "1":
            test_motor("M1 (izquierdo)", hw.set_left)
        elif opt == "2":
            test_motor("M2 (derecho)", hw.set_right)
        elif opt == "3":
            test_motor("Rodillo", hw.set_rodillo)
        elif opt == "4":
            test_encoders()
        elif opt == "5":
            test_kick()
        elif opt == "6":
            test_leds()
        elif opt == "0":
            break
        else:
            print("Opcion invalida.")
    hw.stop_all()
    print("Fin de las pruebas.")


if __name__ == "__main__":
    main()
