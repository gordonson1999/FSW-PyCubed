import ulab.numpy as np
from pycubed import cubesat
from math import *


class IMUSensor:
    def read(self):
        magnetic_field = cubesat.magnetic
        angular_rate = cubesat.gyro
        return magnetic_field, angular_rate

    def status(self):
        # Placeholder for checking IMU status
        return True


class Magnetorquer:
    def status(self):
        # Placeholder for checking magnetorquer status
        return True

    def command(self, ctrl_commands):
        print(f"Commanding magnetorquer with: {ctrl_commands}")
        # Placeholder for sending commands to the magnetorquer


class Battery:
    def status(self):
        # Placeholder for checking battery level
        return True


class DetumbleStateMachine:
    def __init__(self):
        self.imu = IMUSensor()
        self.magnetorquer = Magnetorquer()
        self.battery = Battery()
        # self.system_state = get_system_state()

    def run(self):
        if not self.check_status():
            print("System check failed. Halting.")
        else:
            magnetic_field, angular_rate = self.read_sensors()
            print('magnetic_field', magnetic_field)
            print('angular_rate',angular_rate)
            if not all(np.isfinite(magnetic_field)) or not all(
                np.isfinite(angular_rate)
            ):
                print("Sensor reading invalid. Halting.")
            else:
                any_over_limit = any(abs(rate) > (3*np.pi/180) for rate in angular_rate)
                if any_over_limit:
                    ctrl_commands = self.calculate_control_dipole(magnetic_field, angular_rate)
                    self.issue_commands(ctrl_commands)
                else:
                    print("No need to detumble")

    def read_sensors(self):
        magnetic_field, angular_rate = self.imu.read()
        return 1e-6*np.array(magnetic_field), np.array(angular_rate)*np.pi / 180

    def check_status(self):
        return self.magnetorquer.status() and self.battery.status()

    def issue_commands(self, ctrl_commands):
        self.magnetorquer.command(ctrl_commands)

    def saturate_mag_dipole(self, b_cross_control_dipole, maximum_dipole_moment=0.15):
        for i in range(len(b_cross_control_dipole)):
            if b_cross_control_dipole[i] > maximum_dipole_moment:
                b_cross_control_dipole[i] = maximum_dipole_moment
            elif b_cross_control_dipole[i] < -maximum_dipole_moment:
                b_cross_control_dipole[i] = -maximum_dipole_moment
        return b_cross_control_dipole

    def calculate_control_dipole(self, gyro, mag, k=1.5e-5):
        B_norm = np.linalg.norm(mag)
        b = mag / B_norm
        commanded_mag_dipole_moment = (k / B_norm) * np.cross(gyro, b)
        if all(np.isfinite(commanded_mag_dipole_moment)):
            return commanded_mag_dipole_moment
        return [0, 0, 0]


if __name__ == "__main__":
    detumble_system = DetumbleStateMachine()
    detumble_system.run()
