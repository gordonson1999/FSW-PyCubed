import time
import board, microcontroller
import random
from collections import OrderedDict
import time


from apps.data_handler import DataHandler


fm = DataHandler()

# Just for debug purposes - need initial SD card scan 
#fm.delete_all_files()


print("SD Card Directories: ", fm.list_directories())
fm.register_data_process("log", "fBBBB", True, line_limit=20)
fm.register_data_process("imu", "ffff", True, line_limit=10)
print("SD Card Directories: ", fm.list_directories())


i = 0
MAX_STEP = 10

fm.print_directory()

# To generate random boolean
rb = lambda : random.getrandbits(1)


print("STARTING LOOP")
######################### MAIN LOOP ##############################
while False:

    print("STEP ", i+1)
    
    # Create fake data according to the specified formatting
    log_data = OrderedDict({'time': time.time(), 'a_status': rb(), 'b_status': rb(), 'c_status': rb(), 'd_status': rb()})
    fm.log_data("log", *log_data.values())

    imu_data = OrderedDict({'time': time.time(), 'gyro': random.random(), 'acc': random.random(), 'mag': random.random()})
    fm.log_data("imu", *imu_data.values())

    print("Current file size log: ", fm.get_current_file_size('log'))
    print("Current file size imu: ", fm.get_current_file_size('imu'))
    
    print("latest imu: ", fm.get_latest_data("imu"))

    time.sleep(1)

    i += 1

    if i > MAX_STEP:
        break

# test clean-up

log_data = OrderedDict({'time': time.time(), 'a_status': rb(), 'b_status': rb(), 'c_status': rb(), 'd_status': rb()})
fm.log_data("log", *log_data.values())
fm.log_data("log", *log_data.values())
fm.log_data("log", *log_data.values())
fm.log_data("log", *log_data.values())
time.sleep(2)

path = fm.request_TM_path("log")

print("Exclusion list: ", fm.data_process_registry["log"].excluded_paths)

fm.log_data("log", *log_data.values())

fm.notify_TM_path("log", path)
print("Deletion list: ", fm.data_process_registry["log"].delete_paths)

fm.log_data("log", *log_data.values())

fm.print_directory()

fm.clean_up()
fm.log_data("log", *log_data.values())


print("Current file size log: ", fm.get_current_file_size('log'))


print("SD directories and files...")

fm.print_directory()

print("FINISHED.")

    
