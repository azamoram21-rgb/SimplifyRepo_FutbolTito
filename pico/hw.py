from machine import Pin, PWM
import time

# Polaridad de las ruedas: 1 o -1. Ajustar segun lo que se vea en test.py.
LEFT_SIGN = 1
RIGHT_SIGN = -1

PWM_FREQ = 20_000

KICK_MS = 80              # duracion maxima del pulso del kicker
KICK_COOLDOWN_MS = 500    # tiempo minimo entre disparos
KICK_DUTY = 100           # potencia del kicker (0-100)

# ---- LEDs ----
# OJO: los pines 18 y 19 ahora los usa el dribbler, asi que se quitan
# led_amarillo y led_azul. Si los necesitas, muevelos a pines libres.
led = Pin("LED", Pin.OUT)
led_verde = Pin(20, Pin.OUT)

# ---- STBY (no aparece en las fotos: se mantiene el pin 3 de antes) ----
STBY_PIN = 3
stby = Pin(STBY_PIN, Pin.OUT)

# ---- Puente H 1 / Motor izquierdo ----
mi_ain1 = Pin(4, Pin.OUT)
mi_ain2 = Pin(8, Pin.OUT)
mi_pwm = PWM(Pin(9))
mi_enc_a = Pin(10, Pin.IN, Pin.PULL_UP)
mi_enc_b = Pin(11, Pin.IN, Pin.PULL_UP)

# ---- Puente H 1 / Motor derecho ----
md_ain1 = Pin(6, Pin.OUT)
md_ain2 = Pin(7, Pin.OUT)
md_pwm = PWM(Pin(5))
md_enc_a = Pin(0, Pin.IN, Pin.PULL_UP)
md_enc_b = Pin(1, Pin.IN, Pin.PULL_UP)

# ---- Puente H 2 / Dribbler (rodillo) ----
dr_ain1 = Pin(12, Pin.OUT)
dr_ain2 = Pin(18, Pin.OUT)
dr_pwm = PWM(Pin(20))

# ---- Puente H 2 / Kicker ----
ki_ain1 = Pin(13, Pin.OUT)
ki_ain2 = Pin(14, Pin.OUT)
ki_pwm = PWM(Pin(15))

for _p in (mi_pwm, md_pwm, dr_pwm, ki_pwm):
    _p.freq(PWM_FREQ)

stby.value(1)   # habilita los drivers

led_verde.off()
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
    _set_motor(duty * LEFT_SIGN, mi_ain1, mi_ain2, mi_pwm)


def set_right(duty):
    _set_motor(duty * RIGHT_SIGN, md_ain1, md_ain2, md_pwm)


def set_rodillo(duty):
    _set_motor(duty, dr_ain1, dr_ain2, dr_pwm)


def _kicker_off():
    _set_motor(0, ki_ain1, ki_ain2, ki_pwm)


def stop_all():
    _set_motor(0, mi_ain1, mi_ain2, mi_pwm)
    _set_motor(0, md_ain1, md_ain2, md_pwm)
    _set_motor(0, dr_ain1, dr_ain2, dr_pwm)
    _kicker_off()


_kick_off_at = None
_kick_ready_at = 0


def kick():
    """Dispara el kicker. No hace nada si sigue en cooldown. No bloquea:
    hay que llamar kick_update() seguido para que se apague solo."""
    global _kick_off_at, _kick_ready_at
    now = time.ticks_ms()
    if time.ticks_diff(now, _kick_ready_at) < 0:
        return False
    _set_motor(KICK_DUTY, ki_ain1, ki_ain2, ki_pwm)
    _kick_off_at = time.ticks_add(now, KICK_MS)
    _kick_ready_at = time.ticks_add(now, KICK_MS + KICK_COOLDOWN_MS)
    return True


def kick_update():
    """Llamar en cada vuelta del loop principal para apagar el kicker
    cuando corresponda."""
    global _kick_off_at
    if _kick_off_at is not None and time.ticks_diff(time.ticks_ms(), _kick_off_at) >= 0:
        _kicker_off()
        _kick_off_at = None