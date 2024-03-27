from hal.pycubed import hardware
from tasks.template_task import DebugTask

import time


class Task(DebugTask):

    name = 'IMU'
    ID = 0x05


    curr_time = time.monotonic_ns()

    async def main_task(self):

        print(f'[{self.ID}][{self.name}] Reading BMX160.')

        readings = {
            'accel': hardware.acceleration,
            'mag':   hardware.magnetic,
            'gyro':  hardware.gyro,
        }

        prev_time = self.curr_time
        self.curr_time = time.monotonic_ns()
        data_cache = {'imu':readings}

        # Temp
        print(f'[{self.ID}][{self.name}] Frequency check: {self.curr_time - prev_time}')
        print(f'[{self.ID}][{self.name}] Data: {data_cache}')
        
