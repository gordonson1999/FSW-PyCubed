import time
import board, microcontroller
import random
from collections import OrderedDict

from file_manager import FileManager


fm = FileManager(board.SPI(), board.SD_CS)

# Just for debug purposes - need initial SD card scan 
fm.delete_all_files()


print("SD Card Directories: ", fm.list_directories())
fm.register_file_process("log", "fBBBB", line_limit=20)
fm.register_file_process("imu", "ffff", line_limit=10)
fm.register_file_process("sun", "ffffB", line_limit=15)
print("SD Card Directories: ", fm.list_directories())


i = 0
MAX_STEP = 100

fm.print_directory()

# To generate random boolean
rb = lambda : random.getrandbits(1)


print("STARTING LOOP")
######################### MAIN LOOP ##############################
while True:

    print("STEP ", i+1)
    
    # Create fake data according to the specified formatting
    log_data = OrderedDict({'time': time.time(), 'a_status': rb(), 'b_status': rb(), 'c_status': rb(), 'd_status': rb()})
    fm.log_data("log", *log_data.values())

    imu_data = OrderedDict({'time': time.time(), 'gyro': random.random(), 'acc': random.random(), 'mag': random.random()})
    fm.log_data("imu", *imu_data.values())

    sun_data = OrderedDict({'time': time.time(), 'x': random.random(), 'y': random.random(), 'z': random.random(), 'eclipse': rb()})
    fm.log_data("sun", *sun_data.values())


    print("Current file size log: ", fm.get_current_file_size('log'))
    print("Current file size imu: ", fm.get_current_file_size('imu'))
    print("Current file size sun: ", fm.get_current_file_size('sun'))
    

    time.sleep(1)

    i += 1

    if i > MAX_STEP:
        break

print("SD directories and files...")

fm.print_directory()
#print(fm.file_process_registry["sun"].read_current_file())

print("FINISHED.")

    
