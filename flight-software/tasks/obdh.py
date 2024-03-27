# Onboard Data Handling (OBDH) Task

from tasks.template_task import DebugTask

from state_manager import state_manager as SM
from apps.data_handler import DataHandler as DH

class Task(DebugTask):

    name = 'OBDH'
    ID = 0x02

    scanned_SD = False
    

    async def main_task(self):

        if SM.current_state == 'STARTUP':
            DH.delete_all_files()
            if self.scanned_SD == False:
                DH.scan_SD_card()
                self.scanned_SD = True
            # TODO Temporarily start global state switch here
            SM.switch_to('NOMINAL')
        """elif SM.current_state == 'NOMINAL':
            DH.clean_up()"""


        print(f'[{self.ID}][{self.name}] OBDH running.')

