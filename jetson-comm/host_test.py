from jetson_comm import Message
import serial
import time
from jetson_comm import JetsonComm
import keyboard

def cleanup(uart):
    uart.close()

if __name__ == "__main__":
    uart = serial.Serial('COM8', 9600)
    print("Connected to COM8")
    keyboard.on_press_key("q", lambda _: cleanup(uart))
    jetson_comm = JetsonComm(uart)
    message = jetson_comm.receive_message()
    message = message.decode('utf-8')    
    print(f"Received message: {message}")