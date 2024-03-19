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
SAT_HEARTBEAT = 0x01

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

    if(lora_tx_message_ID == SAT_HEARTBEAT):
        # Construct SAT heartbeat 
        lora_tx_message = [SAT_HEARTBEAT, 0x00, 0x01, 0x0F] 

        # Generate LoRa payload for SAT heartbeat 
        # Add system status
        system_status = get_system_status()
        lora_tx_message += system_status

        # Add satellite battery SOC
        batt_soc = get_batt_soc()
        lora_tx_message.append(batt_soc)

        # Add satellite temperature 
        temperature = get_temperature()
        lora_tx_message.append(temperature)

        # Add satellite latitude 
        sat_lat = get_lat()
        lora_tx_message += sat_lat

        # Add satellite longitude  
        sat_long = get_long()
        lora_tx_message += sat_long

        # Add no request from satellite 
        lora_tx_message += [0x00, 0x00, 0x00]

    elif(lora_tx_message_ID == GS_ACK):
        # Construct GS acknowledgement 
        lora_tx_message = [GS_ACK, 0x00, 0x01, 0x04] 

        # Generate LoRa payload for GS acknowledgement  
        # Add received message ID
        prev_message_ID = get_prev_message_ID()
        lora_tx_message.append(prev_message_ID)

        # Add received message ID
        req_message_ID = get_req_message_ID()
        lora_tx_message.append(req_message_ID)

        # Add received message ID
        req_message_sq = get_req_message_sq()
        lora_tx_message += req_message_sq
    
    return bytes(lora_tx_message)

def deconstruct_message(lora_rx_message):
    """
    :param lora_rx_message: Received LoRa message
    :return: None

    Deconstructs RX message based on message ID
    """
    # check RX message ID 
    if(lora_rx_message[0] == SAT_HEARTBEAT):
        # received satellite heartbeat, deconstruct header 
        print("GS: Received SAT heartbeat!")
        sq = (lora_rx_message[1] << 8) + lora_rx_message[2]
        print("GS: Sequence Count:", sq)
        print("GS: Message Length:", lora_rx_message[3])

        # deconstruct message contents 
        print("GS: Satellite system status:", lora_rx_message[4], lora_rx_message[5])
        print("GS: Satellite battery SOC: " + str(lora_rx_message[6]) + "%")
        print("GS: Satellite temperature: " + str(lora_rx_message[7]) + "*C")
        sat_lat = convert_floating_point(lora_rx_message[8:12])
        sat_long = convert_floating_point(lora_rx_message[12:16])
        print("GS: Satellite is at: " + str(sat_lat) + ", " + str(sat_long))
        sq = (lora_rx_message[17] << 8) + lora_rx_message[18]
        print("GS: Satellite request: " + str(lora_rx_message[16]) + ", packet: " + str(sq))

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

"""
Dummy Low Level Interface Functions
===================================
Placeholders for FSW API to get information for telemetry
Delete when this code is integrated with CircuitPython FSW / GS software 
"""

def get_system_status():
    # Return system status
    return [0x1F, 0xFF]

def get_batt_soc():
    # Return battery SOC % 
    return 80

def get_temperature():
    # Return satellite temp in *C
    return 16

def get_lat(): 
    # Return satellite latitude 
    sat_lat = 40.445
    return convert_fixed_point(sat_lat)

def get_long():
    # Return satellite longitude 
    sat_long = -79.945278
    return convert_fixed_point(sat_long)

def get_prev_message_ID():
    # Return the previous message received 
    return 0x01

def get_req_message_ID():
    # Return requested message ID
    return 0x01 

def get_req_message_sq():
    # Return requested message sequence count 
    return [0x00, 0x001]