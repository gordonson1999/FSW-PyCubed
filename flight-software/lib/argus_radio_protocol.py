"""
'argus_radio_protocol.py'
======================
Python package containing protocol constants (IDs etc.). 
Also contains functions for constructing/deconstructing 
protocol messages. 

Each message has the following header: 
MESSAGE_ID : 1 byte 
SEQ_COUNT  : 2 bytes
LENGTH     : 1 byte  

Authors: DJ Morvay, Akshat Sahay
"""

# PyCubed Board Lib
from pycubed import cubesat

# Message ID definitions 
SAT_HEARTBEAT_BATT  = 0x00
SAT_HEARTBEAT_SUN   = 0x01
SAT_HEARTBEAT_IMU   = 0x02
SAT_HEARTBEAT_GPS   = 0x03

GS_ACK  = 0x08
SAT_ACK = 0x09

SAT_IMAGES   = 0x21
SAT_DEL_IMG1 = 0x22
SAT_DEL_IMG2 = 0x23
SAT_DEL_IMG3 = 0x24

SAT_IMG1_CMD = 0x50
SAT_IMG2_CMD = 0x51
SAT_IMG3_CMD = 0x52

class IMAGES:
    def __init__(self):
        # Image #1 declarations
        self.image_1_CMD_ID = 0x50
        self.image_1_UID = 0x0
        self.image_1_size = 0
        self.image_1_message_count = 0
        # Image #2 declarations
        self.image_2_CMD_ID = 0x51
        self.image_2_UID = 0x0
        self.image_2_size = 0
        self.image_2_message_count = 0
        # Image #3 declarations
        self.image_3_CMD_ID = 0x52
        self.image_3_UID = 0x0
        self.image_3_size = 0
        self.image_3_message_count = 0

def construct_message(lora_tx_message_ID):
    """
    :param lora_tx_message_ID: LoRa message ID
    :return: lora_tx_message

    Constructs TX message based on message ID
    """
    # LoRa header
    lora_tx_message = [0x00, 0x00, 0x00, 0x00] 

    if(lora_tx_message_ID == SAT_HEARTBEAT_BATT):
        # Construct SAT heartbeat 
        lora_tx_message = [SAT_HEARTBEAT, 0x00, 0x00, 0x0F]

        # Generate LoRa payload for SAT heartbeat 
        # Add system status
        lora_tx_message += [0x00, 0x00]

        # Add battery SOCs, 1 byte for each battery 
        lora_tx_message += [0x53, 0x51, 0x47, 0x61, 0x52, 0x51]

        # Add current as float
        lora_tx_message += convert_fixed_point(891.18)

        # Add reboot count and payload status
        lora_tx_message += [0x00, 0x00]

        # Add time reference as uint32_t 
        lora_tx_message += [0x65, 0xF9, 0xE8, 0x4A]
    
    return bytes(lora_tx_message)

def deconstruct_message(lora_rx_message):
    """
    :param lora_rx_message: Received LoRa message
    :return: None

    Deconstructs RX message based on message ID
    """
    # check RX message ID 
    elif(lora_rx_message[0] == GS_ACK):
        print("SAT: Received GS ack!")
        sq = (lora_rx_message[1] << 8) + lora_rx_message[2]
        print("SAT: Sequence Count:", sq)
        print("SAT: Message Length:", lora_rx_message[3])

        # deconstruct message contents
        print("SAT: GS received message:", hex(lora_rx_message[4]))
        print("SAT: GS requested message:", hex(lora_rx_message[5]))
        sq = (lora_rx_message[6] << 8) + lora_rx_message[7]
        print("SAT: GS requested sequence count:", sq)

### Helper functions for converting to FP format and back ###
def convert_fixed_point(val):
    message_list = []
    neg_bit_flag = 0

    # If val -ve, convert to natural, set first bit of MSB 
    if(val < 0):
        val = -1 * val
        neg_bit_flag = 1

    # Isolate int and write to two bytes 
    val_int = int(val)
    val_int_LSB = val_int & 0xFF
    val_int_MSB = (val_int >> 8) & 0xFF

    # Set MSB first bit as neg_bit_flag
    val_int_MSB |= (neg_bit_flag << 7)

    # Add the values to the test list 
    message_list.append(val_int_MSB)
    message_list.append(val_int_LSB)

    # Isolate decimal and write to bytes
    val_dec = val - val_int
    val_dec = int(val_dec * 65536)
    val_dec_LSB = val_dec & 0xFF
    val_dec_MSB = (val_dec >> 8) & 0xFF

    # Add the values to the test list 
    message_list.append(val_dec_MSB)
    message_list.append(val_dec_LSB)

    return message_list

def convert_floating_point(message_list):
    val = 0
    neg_bit_flag = 0

    # Check -ve, extract LSB bytes for val, combine 
    if((message_list[0] and (1 << 7) >> 7) == 1): 
        message_list[0] &= 0x7F
        neg_bit_flag = 1

    # Extract bytes for val, combine 
    val += (message_list[0] << 8) + message_list[1]
    val += ((message_list[2] << 8) + message_list[3]) / 65536
    if(neg_bit_flag == 1): val = -1 * val

    return val