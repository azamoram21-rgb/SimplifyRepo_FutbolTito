"""
Clase con la interfaz minima de cv2.VideoCapture (.isOpened / .read /
.release), pero leyendo frames desde memoria compartida en vez de una
camara real. Permite que autonomous/vision.py no note la diferencia entre
esto y una camara de verdad.

Requiere que simulator/run_simulator.py este corriendo (es quien crea la
memoria compartida).
"""

from multiprocessing import shared_memory
import numpy as np

from camera_sim import WIDTH, HEIGHT, CHANNELS

SHM_NAME = "irb1010_sim_cam"


class SimCapture:
    def __init__(self, width=WIDTH, height=HEIGHT, channels=CHANNELS, name=SHM_NAME):
        try:
            self._shm = shared_memory.SharedMemory(name=name)
        except FileNotFoundError:
            raise FileNotFoundError(
                "No se encontro la camara simulada. Corre primero "
                "'python run_simulator.py' en la carpeta simulator/."
            )
        self._frame = np.ndarray(
            (height, width, channels), dtype=np.uint8, buffer=self._shm.buf
        )

    def isOpened(self):
        return True

    def read(self):
        # copiar para no exponer el buffer compartido directamente
        return True, self._frame.copy()

    def release(self):
        self._shm.close()
