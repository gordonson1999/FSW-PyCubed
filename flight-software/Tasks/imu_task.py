from Tasks.template_task import Task
from pycubed import cubesat
import ulab.numpy as np

class task(Task):
    priority = 5
    frequency = 1
    name='imu'
    color = 'green'

    def __init__(self,satellite):
        super().__init__(satellite)
        self.data_file=self.cubesat.new_file('/data/imu',binary=True)
        self.window_size = 5  # Adjust as needed
        self.data_buffer_gyro = []
        self.data_buffer_acc = []
        self.data_buffer_mag = []
        self.buffer_index = 0
    async def main_task(self):
        filtered_gyro = await self.moving_average_filter(self.cubesat.gyro,self.data_buffer_gyro)
        filtered_acc = await self.moving_average_filter(self.cubesat.acceleration,self.data_buffer_acc)
        filtered_mag = await self.moving_average_filter(self.cubesat.magnetic,self.data_buffer_mag)
        print('filtered_gyro', filtered_gyro)
        print('filtered_acc', filtered_acc)
        print('filtered_mag', filtered_mag)
        readings = {
            'accel':filtered_acc,
            'mag':  filtered_mag,
            'gyro': filtered_gyro,
        }
        
        self.cubesat.data_cache.update({'imu':readings})
        # print the readings with some fancy formatting
        self.debug('IMU readings (x,y,z)')
        for imu_type in self.cubesat.data_cache['imu']:
            self.debug(f"{imu_type:>5} {self.cubesat.data_cache['imu'][imu_type]}",2)
    
    async def moving_average_filter(self,new_data,data_buffer):
        data_buffer.append(new_data)
        if len(data_buffer) > self.window_size:
            data_buffer.pop(0)  # Remove the oldest data point
        
        self.num_samples = len(data_buffer)
        avg_data = [sum(axis[i] for axis in data_buffer) / self.num_samples for i in range(len(new_data))]
        return avg_data