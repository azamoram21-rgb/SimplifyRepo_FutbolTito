"""
Servidor TCP que imita firmware/main.py pero corriendo en el PC: mismo
protocolo ("vl,vr,sol,rod\\n", framing por linea, watchdog), solo que
mueve hw_sim (fisica) en vez de pines reales. Corre en un thread aparte
para no bloquear el loop de fisica/render de run_simulator.py.
"""

import socket
import threading
import time

import hw_sim

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8080
WATCHDOG_MS = 500
RECV_TIMEOUT_S = 0.1


def _client_loop(conn):
    conn.settimeout(RECV_TIMEOUT_S)
    buf = b""
    prev_sol = 0
    last_msg_ms = time.monotonic() * 1000

    while True:
        now_ms = time.monotonic() * 1000
        if now_ms - last_msg_ms > WATCHDOG_MS:
            hw_sim.stop_all()

        try:
            chunk = conn.recv(256)
        except socket.timeout:
            chunk = None
        except OSError:
            break

        if chunk == b"":
            print("[simulador] main_sim.py se desconecto")
            break

        if chunk:
            buf += chunk
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                parts = line.split(b",")
                if len(parts) != 4:
                    continue
                try:
                    vl, vr, sol_val, rod_val = (int(p) for p in parts)
                except ValueError:
                    continue

                hw_sim.set_left(vl)
                hw_sim.set_right(vr)
                hw_sim.set_rodillo(rod_val)
                if sol_val and not prev_sol:
                    hw_sim.kick()
                prev_sol = sol_val
                last_msg_ms = time.monotonic() * 1000

    hw_sim.stop_all()
    conn.close()


def start_server_thread():
    """Arranca el servidor TCP en un thread daemon (no bloqueante)."""

    def _accept_loop():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((SERVER_HOST, SERVER_PORT))
        s.listen(1)
        print(f"[simulador] Servidor TCP escuchando en {SERVER_HOST}:{SERVER_PORT}")
        while True:
            conn, addr = s.accept()
            print(f"[simulador] main_sim.py conectado desde {addr}")
            threading.Thread(target=_client_loop, args=(conn,), daemon=True).start()

    t = threading.Thread(target=_accept_loop, daemon=True)
    t.start()
    return t
