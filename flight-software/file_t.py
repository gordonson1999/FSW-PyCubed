import time
import board, microcontroller
import random
from collections import OrderedDict
import time


from apps.data_handler import DataHandler as DH


dh = DH()

# Just for debug purposes - need initial SD card scan 
#dh.delete_all_files()


print("SD Card Directories: ", dh.list_directories())
dh.register_data_process("log", "fBBBB", True, line_limit=20)
dh.register_data_process("imu", "ffff", True, line_limit=10)
print("SD Card Directories: ", dh.list_directories())


i = 0
MAX_STEP = 10

dh.print_directory()

# To generate random boolean
rb = lambda : random.getrandbits(1)


print("STARTING LOOP")
######################### MAIN LOOP ##############################
while False:

    print("STEP ", i+1)
    
    # Create fake data according to the specified formatting
    log_data = OrderedDict({'time': time.time(), 'a_status': rb(), 'b_status': rb(), 'c_status': rb(), 'd_status': rb()})
    dh.log_data("log", *log_data.values())

    imu_data = OrderedDict({'time': time.time(), 'gyro': random.random(), 'acc': random.random(), 'mag': random.random()})
    dh.log_data("imu", *imu_data.values())

    print("Current file size log: ", dh.get_current_file_size('log'))
    print("Current file size imu: ", dh.get_current_file_size('imu'))
    
    print("latest imu: ", dh.get_latest_data("imu"))

    time.sleep(1)

    i += 1

    if i > MAX_STEP:
        break

# test clean-up

log_data = OrderedDict({'time': time.time(), 'a_status': rb(), 'b_status': rb(), 'c_status': rb(), 'd_status': rb()})
dh.log_data("log", *log_data.values())
dh.log_data("log", *log_data.values())
dh.log_data("log", *log_data.values())
dh.log_data("log", *log_data.values())
time.sleep(2)

path = dh.request_TM_path("log")

print("Exclusion list: ", dh.data_process_registry["log"].excluded_paths)

dh.log_data("log", *log_data.values())

dh.notify_TM_path("log", path)
print("Deletion list: ", dh.data_process_registry["log"].delete_paths)

dh.log_data("log", *log_data.values())

dh.print_directory()

dh.clean_up()
dh.log_data("log", *log_data.values())


print("Current file size log: ", dh.get_current_file_size('log'))


print("SD directories and files...")

dh.print_directory()

print("FINISHED.")

    
