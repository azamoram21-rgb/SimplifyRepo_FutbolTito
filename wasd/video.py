"""
Receptor de video MJPEG desde la Raspberry Pi (ver camera_server.py).

Corre en un hilo aparte para no frenar el envio de comandos al robot. Solo
guarda los bytes del ultimo JPEG; decodificarlo y mostrarlo es trabajo de
quien lo use (main.py lo hace con pygame). El PC no procesa imagen.
"""

import threading
import time
import urllib.request

PI_IP = "192.168.4.50"     # IP fija de la Pi en la red del robot (ver instrucciones)
PI_PORT = 8000
VIDEO_URL = "http://{}:{}/stream".format(PI_IP, PI_PORT)


class VideoStream:
    def __init__(self, url=VIDEO_URL):
        self.url = url
        self.error = None            # ultimo error de conexion, para mostrarlo en pantalla
        self._lock = threading.Lock()
        self._jpeg = None
        self._seq = 0
        self._t = None               # momento (monotonic) del ultimo frame recibido
        self._stop = threading.Event()
        threading.Thread(target=self._run, daemon=True).start()

    def latest(self):
        """Devuelve (numero_de_frame, bytes_jpeg_o_None)."""
        with self._lock:
            return self._seq, self._jpeg

    def age(self):
        """Segundos desde el ultimo frame recibido (inf si nunca llego uno)."""
        with self._lock:
            t = self._t
        return float("inf") if t is None else time.monotonic() - t

    def close(self):
        self._stop.set()

    def _publish(self, jpeg):
        with self._lock:
            self._jpeg = jpeg
            self._seq += 1
            self._t = time.monotonic()

    @staticmethod
    def _extract(buf, publish):
        """Saca de `buf` todos los JPEG completos (SOI ff d8 ... EOI ff d9) y
        devuelve lo que sobra."""
        while True:
            a = buf.find(b"\xff\xd8")
            if a == -1:
                return buf[-1:]          # por si el marcador quedo partido entre chunks
            b = buf.find(b"\xff\xd9", a + 2)
            if b == -1:
                return buf[a:]
            publish(buf[a:b + 2])
            buf = buf[b + 2:]

    def _run(self):
        # Sin proxy: si el PC tiene uno configurado, no debe interferir con la red del robot.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        while not self._stop.is_set():
            try:
                with opener.open(self.url, timeout=3) as resp:
                    self.error = None
                    buf = b""
                    while not self._stop.is_set():
                        chunk = resp.read1(65536)
                        if not chunk:
                            raise ConnectionError("la Pi cerro el stream")
                        buf = self._extract(buf + chunk, self._publish)
                        if len(buf) > 2_000_000:
                            buf = b""    # basura sin marcadores: descartar
            except Exception as e:
                self.error = str(e) or type(e).__name__
                self._stop.wait(1.0)     # reintentar cada segundo