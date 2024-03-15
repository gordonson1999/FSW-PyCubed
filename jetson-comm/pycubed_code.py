import usb_cdc
import json 
from jetson_comm import Message
from jetson_comm import JetsonComm

data_console = usb_cdc.data
data_console.timeout = 0
counter = 0

MAX_MESSAGE_RUN = 10

data_console.reset_input_buffer()
data_console.reset_output_buffer()
            
if __name__ == "__main__":
    print("Bootstrapped")
    uart = JetsonComm(data_console)
    message = Message(0x0, "Hello World".encode())
    uart.send_message(message)
    print("Message sent")