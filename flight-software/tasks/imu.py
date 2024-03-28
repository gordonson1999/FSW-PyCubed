from hal.pycubed import hardware

from tasks.template_task import DebugTask

from state_manager import state_manager as SM
from apps.data_handler import DataHandler as DH



import time


class Task(DebugTask):

    name = 'IMU'
    ID = 0x05

    # Temporary fake time
    curr_time = time.monotonic_ns()

    async def main_task(self):


        if SM.current_state == 'NOMINAL':

            if DH.data_process_exists("imu") == False:
                DH.register_data_process("imu", "ffffffffff", True, line_limit=20)
                #time.sleep(50000)

            print(f'[{self.ID}][{self.name}] Reading BMX160.')


            prev_time = self.curr_time
            self.curr_time = time.monotonic_ns()


            readings = {
                'time':  time.time(), # temporary fake time
                'accel': hardware.acceleration,
                'mag':   hardware.magnetic,
                'gyro':  hardware.gyro
            }

            log_data = {
                'time':  time.time(), # temporary fake time
                'accel_x': readings['accel'][0],
                'accel_y': readings['accel'][1],
                'accel_z': readings['accel'][2],
                'mag_x': readings['mag'][0],
                'mag_y': readings['mag'][1],
                'mag_z': readings['mag'][2],
                'gyro_x': readings['gyro'][0],
                'gyro_y': readings['gyro'][1],
                'gyro_z': readings['gyro'][2]
            }


            DH.log_data("imu", *log_data.values())

            # Temp
            print(f'[{self.ID}][{self.name}] Frequency check: {self.curr_time - prev_time}')
            print(f'[{self.ID}][{self.name}] Data: {readings}')
        
