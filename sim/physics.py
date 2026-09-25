"""
Fisica simple de un robot diferencial y una pelota, sin hardware.

Expone .pos / .angle igual que pc/vision.py (Robot/Ball), para poder correr
behaviors.py sin ningun cambio. No busca ser fisicamente exacto: solo sirve
para probar y calibrar la logica de las rutinas antes de ir a la cancha.
"""

import math

LINEAR_SCALE = 1.5    # duty promedio -> velocidad lineal (px/s)
ANGULAR_SCALE = 4.0    # diferencia de duty -> velocidad angular (deg/s)
FRICTION = 0.98
BOUNCE = 0.6


class SimRobot:
    def __init__(self, x, y, theta_deg=0.0):
        self.x = x
        self.y = y
        self.theta = theta_deg

    @property
    def pos(self):
        return (int(self.x), int(self.y))

    @property
    def angle(self):
        return self.theta

    def step(self, vl, vr, dt):
        v = (vl + vr) / 2.0 * LINEAR_SCALE
        w = (vr - vl) * ANGULAR_SCALE
        rad = math.radians(self.theta)
        self.x += v * math.cos(rad) * dt
        self.y += v * math.sin(rad) * dt
        self.theta = (self.theta + w * dt) % 360


class SimBall:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0

    @property
    def pos(self):
        return (int(self.x), int(self.y))

    def step(self, dt, bounds):
        self.vx *= FRICTION
        self.vy *= FRICTION
        self.x += self.vx * dt
        self.y += self.vy * dt

        w, h = bounds
        if self.x < 0 or self.x > w:
            self.vx *= -BOUNCE
            self.x = max(0, min(self.x, w))
        if self.y < 0 or self.y > h:
            self.vy *= -BOUNCE
            self.y = max(0, min(self.y, h))

    def kick_from(self, robot, power=250.0):
        rad = math.radians(robot.angle)
        self.vx += power * math.cos(rad)
        self.vy += power * math.sin(rad)
