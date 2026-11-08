"""
Cliente TCP: PC -> Pico. El Pico levanta su propio Access Point (ver
firmware/main.py) y hace de servidor; el PC se conecta a esa red y a este
socket. Protocolo: "vl,vr,sol,rod\n" (vl/vr duty -100..100, sol 0/1,
rod duty rodillo 0..100).
"""

import socket

ROBOT_IP = "192.168.4.1"   # IP por defecto del AP de MicroPython
ROBOT_PORT = 8080


class RobotLink:
    def __init__(self, ip=ROBOT_IP, port=ROBOT_PORT):
        self.ip = ip
        self.port = port
        self.sock = None
        self._connect()

    def _connect(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((self.ip, self.port))
            s.settimeout(None)
            self.sock = s
            print(f"Conectado al robot en {self.ip}:{self.port}")
        except OSError as e:
            print(f"No se pudo conectar al robot ({e})")
            self.sock = None

    def send(self, vl, vr, sol, rod):
        line = f"{int(vl)},{int(vr)},{int(sol)},{int(rod)}\n"
        if self.sock is None:
            self._connect()
            return
        try:
            self.sock.send(line.encode())
        except OSError:
            print("Se perdio la conexion, reintentando...")
            self.sock = None

    def close(self):
        if self.sock is not None:
            try:
                self.send(0, 0, 0, 0)
                self.sock.close()
            except OSError:
                pass
