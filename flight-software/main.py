
import sys

for path in ['/hal', '/apps']:
    if path not in sys.path:
        sys.path.append(path)


print("initializing the board...")
from hal.pycubed import hardware
from state_manager import state_manager


"""import time 
from apps.data_handler import DataHandler as DH
DH.delete_all_files()
time.sleep(5000)"""



try:
    # Run forever
    state_manager.start('STARTUP')
    #import obdh_sd_test
except Exception as e:
    print(e)
    # TODO Log the error

