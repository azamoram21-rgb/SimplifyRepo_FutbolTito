"""
El Pico crea su propia red WiFi (Access Point) y hace de servidor TCP.
El PC se conecta directo a esa red (sin router de por medio) y corre
pc/main.py.

Protocolo: lineas de texto "vl,vr,sol,rod\n" (framing por \n).
Si no llega ningun mensaje nuevo en WATCHDOG_MS, el robot se detiene solo.
"""

import network
import socket
import time
import hw

AP_SSID = "FutBot_1"
AP_PASSWORD = "futbot123"   # minimo 8 caracteres (WPA2)
SERVER_PORT = 8080

WATCHDOG_MS = 500
RECV_TIMEOUT_S = 0.1


def start_ap():
    ap = network.WLAN(network.AP_IF)
    ap.config(ssid=AP_SSID, password=AP_PASSWORD)
    ap.active(True)
    while not ap.active():
        time.sleep(0.1)
    hw.led.on()
    print("AP activo. SSID: {}  IP: {}".format(AP_SSID, ap.ifconfig()[0]))
    return ap


def run_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", SERVER_PORT))
    server_socket.listen(1)
    print("Esperando al PC en el puerto", SERVER_PORT)

    while True:
        conn, addr = server_socket.accept()
        conn.settimeout(RECV_TIMEOUT_S)
        print("PC conectado desde", addr)
        hw.led_verde.on()

        buf = b""
        prev_sol = 0
        last_msg_ms = time.ticks_ms()

        while True:
            hw.kick_update()

            if time.ticks_diff(time.ticks_ms(), last_msg_ms) > WATCHDOG_MS:
                hw.stop_all()

            try:
                chunk = conn.recv(256)
            except OSError:
                chunk = None

            if chunk == b"":
                print("PC desconectado")
                break

            if chunk:
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    parts = line.split(b",")
                    if len(parts) != 4:
                        continue
                    try:
                        vl = int(parts[0])
                        vr = int(parts[1])
                        sol_val = int(parts[2])
                        rod_val = int(parts[3])
                    except ValueError:
                        continue

                    hw.set_left(vl)
                    hw.set_right(vr)
                    hw.set_rodillo(rod_val)   # rod ahora es duty (0-100), no solo on/off
                    if sol_val and not prev_sol:
                        hw.kick()
                    prev_sol = sol_val
                    last_msg_ms = time.ticks_ms()

        hw.stop_all()
        hw.led_verde.off()
        conn.close()


def main():
    hw.stop_all()
    start_ap()
    try:
        run_server()
    finally:
        hw.stop_all()


main()
