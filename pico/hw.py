"""
Unico archivo que toca `machine`. Pines + API simple para mover el robot.

Si una rueda gira al reves, corregir aqui (LEFT_SIGN / RIGHT_SIGN),
no recableando ni tocando el resto del codigo.
"""

from machine import Pin, PWM
import time

# Polaridad de las ruedas: 1 o -1. Ajustar segun lo que se vea en test.py.
LEFT_SIGN = 1
RIGHT_SIGN = -1

PWM_FREQ = 20_000

KICK_MS = 80              # duracion maxima del pulso del solenoide
KICK_COOLDOWN_MS = 500    # tiempo minimo entre disparos

# ---- LEDs ----
led = Pin("LED", Pin.OUT)
led_verde = Pin(20, Pin.OUT)
led_amarillo = Pin(19, Pin.OUT)
led_azul = Pin(18, Pin.OUT)

# ---- Driver 1 / Motor 1 (izquierdo) ----
d1_stby = Pin(3, Pin.OUT)
d1_ain1 = Pin(2, Pin.OUT)
d1_ain2 = Pin(1, Pin.OUT)
d1_pwma = PWM(Pin(0))
d1_enc_a = Pin(7, Pin.IN, Pin.PULL_UP)
d1_enc_b = Pin(8, Pin.IN, Pin.PULL_UP)

# ---- Driver 2 / Motor 2 (derecho) + rodillo ----
d2_stby = Pin(11, Pin.OUT)
d2_ain1 = Pin(6, Pin.OUT)
d2_ain2 = Pin(5, Pin.OUT)
d2_pwma = PWM(Pin(4))
d2_enc_a = Pin(9, Pin.IN, Pin.PULL_UP)
d2_enc_b = Pin(10, Pin.IN, Pin.PULL_UP)
d2_bin1 = Pin(12, Pin.OUT)
d2_bin2 = Pin(13, Pin.OUT)
d2_pwmb = PWM(Pin(14))

# ---- Solenoide ----
sol = Pin(15, Pin.OUT)

d1_pwma.freq(PWM_FREQ)
d2_pwma.freq(PWM_FREQ)
d2_pwmb.freq(PWM_FREQ)
d1_stby.value(1)   # habilita driver 1
d2_stby.value(1)   # habilita driver 2
sol.off()

led_verde.off()
led_amarillo.off()
led_azul.off()
led.off()


def _set_motor(duty, ain1, ain2, pwm):
    duty = max(-100, min(100, duty))
    if duty >= 0:
        ain1.value(1)
        ain2.value(0)
    else:
        ain1.value(0)
        ain2.value(1)
    pwm.duty_u16(abs(duty) * 65535 // 100)


def set_left(duty):
    _set_motor(duty * LEFT_SIGN, d1_ain1, d1_ain2, d1_pwma)


def set_right(duty):
    _set_motor(duty * RIGHT_SIGN, d2_ain1, d2_ain2, d2_pwma)


def set_rodillo(duty):
    _set_motor(duty, d2_bin1, d2_bin2, d2_pwmb)


def stop_all():
    _set_motor(0, d1_ain1, d1_ain2, d1_pwma)
    _set_motor(0, d2_ain1, d2_ain2, d2_pwma)
    _set_motor(0, d2_bin1, d2_bin2, d2_pwmb)
    sol.off()


_kick_off_at = None
_kick_ready_at = 0


def kick():
    """Dispara el solenoide. No hace nada si sigue en cooldown. No bloquea:
    hay que llamar kick_update() seguido para que se apague solo."""
    global _kick_off_at, _kick_ready_at
    now = time.ticks_ms()
    if time.ticks_diff(now, _kick_ready_at) < 0:
        return False
    sol.on()
    _kick_off_at = time.ticks_add(now, KICK_MS)
    _kick_ready_at = time.ticks_add(now, KICK_MS + KICK_COOLDOWN_MS)
    return True


def kick_update():
    """Llamar en cada vuelta del loop principal para apagar el solenoide
    cuando corresponda."""
    global _kick_off_at
    if _kick_off_at is not None and time.ticks_diff(time.ticks_ms(), _kick_off_at) >= 0:
        sol.off()
        _kick_off_at = None
