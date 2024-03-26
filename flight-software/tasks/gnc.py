from Tasks.template_task import Task
from pycubed import cubesat
from lib.detumbling_sm import *
import time


class task(Task):
    priority = 5
    frequency = 1 / 10  # once every 10s
    name = "detumble"
    color = "blue"

    rgb_on = False
    last = None

    async def main_task(self):
        """
        Detubling task for the cubesat. Uses B-cross control to detumble the satelite.
        """
        if not self.cubesat.hardware['IMU']:
            return
        # compute control
        # m = bcross(cubesat.magnetic, cubesat.gyro)
        detumble_system = DetumbleStateMachine()
        detumble_system.run()

        self.last = time.monotonic()
