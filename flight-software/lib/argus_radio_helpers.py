"""
'argus_radio_helpers.py'
======================
Satellite radio class for Argus-1 CubeSat. 
Message packing/unpacking for telemetry/image TX
and acknowledgement RX. 

Authors: DJ Morvay, Akshat Sahay
"""

# Common CircuitPython Libs 
import os
import time
import sys

# PyCubed Board Lib
from pycubed import cubesat

# Argus-1 Lib
from argus_radio_protocol import *

class SATELLITE_RADIO:
    '''
        Name: __init__
        Description: Initialization of SATELLITE class
    '''
    def __init__(self):
        self.image_get_info()
        self.send_mod = 10
        self.heartbeat_sent = False
        self.image_deleted = True
        self.last_image_id = 0x00
        self.gs_req_message_ID = SAT_HEARTBEAT
    
    
    '''
        Name: image_get_info
        Description: Read three images from flash, store in buffer
    '''
    def image_get_info(self):
        # Setup image class
        self.sat_images = IMAGES()
        # Setup initial image UIDs
        self.sat_images.image_1_UID = 0x5
        self.sat_images.image_2_UID = 0x2
        self.sat_images.image_3_UID = 0x3

        ## ---------- Image Sizes and Message Counts ---------- ## 
        # Get image #1 size and message count
        image_1_stat = os.stat('/sd/IMAGES/ohio.jpg')
        self.sat_images.image_1_size = int(image_1_stat[6])
        self.sat_images.image_1_message_count = int(self.sat_images.image_1_size / 128)

        if ((self.sat_images.image_1_size % 128) > 0):
            self.sat_images.image_1_message_count += 1    

        print("Image #1 size is", self.sat_images.image_1_size,"bytes")
        print("This image #1 requires",self.sat_images.image_1_message_count,"messages")

        # Get image #2 size and message count
        image_2_stat = os.stat('/sd/IMAGES/tokyo_small.jpg')
        self.sat_images.image_2_size = int(image_2_stat[6])
        self.sat_images.image_2_message_count = int(self.sat_images.image_2_size / 128)

        if ((self.sat_images.image_2_size % 128) > 0):
            self.sat_images.image_2_message_count += 1    

        print("Image #2 size is", self.sat_images.image_2_size,"bytes")
        print("This image #2 requires",self.sat_images.image_2_message_count,"messages")

         # Get image #3 size and message count
        image_3_stat = os.stat('/sd/IMAGES/oregon_small.jpg')
        self.sat_images.image_3_size = int(image_3_stat[6])
        self.sat_images.image_3_message_count = int(self.sat_images.image_3_size / 128)

        if ((self.sat_images.image_3_size % 128) > 0):
            self.sat_images.image_3_message_count += 1    

        print("Image #3 size is", self.sat_images.image_3_size,"bytes")
        print("This image #3 requires",self.sat_images.image_3_message_count,"messages")

    '''
        Name: image_pack_info
        Description: Pack message ID, UID, size, and message count for all images in buffer.
    '''
    def image_pack_info(self):
        return (self.sat_images.image_1_CMD_ID.to_bytes(1,'big') + self.sat_images.image_1_UID.to_bytes(1,'big') + \
                self.sat_images.image_1_size.to_bytes(4,'big') + self.sat_images.image_1_message_count.to_bytes(2,'big') + \
                self.sat_images.image_2_CMD_ID.to_bytes(1,'big') + self.sat_images.image_2_UID.to_bytes(1,'big') + \
                self.sat_images.image_2_size.to_bytes(4,'big') + self.sat_images.image_2_message_count.to_bytes(2,'big') + \
                self.sat_images.image_3_CMD_ID.to_bytes(1,'big') + self.sat_images.image_3_UID.to_bytes(1,'big') + \
                self.sat_images.image_3_size.to_bytes(4,'big') + self.sat_images.image_3_message_count.to_bytes(2,'big'))

    '''
        Name: image_pack_images
        Description: Pack one image into an array
        Inputs:
            IMG_CMD - image requested command
    '''
    def image_pack_images(self,IMG_CMD):
        # Initialize image arrays
        self.image_array = []
        image_1_str = '/sd/IMAGES/ohio.jpg'
        image_2_str = '/sd/IMAGES/tokyo_small.jpg'
        image_3_str = '/sd/IMAGES/oregon_small.jpg'
        
        if (IMG_CMD == SAT_IMG2_CMD):
            # Image #2 Buffer Store
            bytes_remaining = self.sat_images.image_2_size
            send_bytes = open(image_2_str,'rb')
            # Loop through image and store contents in an array
            while (bytes_remaining > 0):
                if (bytes_remaining >= 128):
                    self.image_array.append(send_bytes.read(128))
                else:
                    self.image_array.append(send_bytes.read(bytes_remaining))
                    
                bytes_remaining -= 128
            # Close file when complete
            send_bytes.close()
        elif (IMG_CMD == SAT_IMG3_CMD):
            # Image #3 Buffer Store
            bytes_remaining = self.sat_images.image_3_size
            send_bytes = open(image_3_str,'rb')
            # Loop through image and store contents in an array
            while (bytes_remaining > 0):
                if (bytes_remaining >= 128):
                    self.image_array.append(send_bytes.read(128))
                else:
                    self.image_array.append(send_bytes.read(bytes_remaining))
                    
                bytes_remaining -= 128
            # Close file when complete
            send_bytes.close()
        else:
            # Image #1 Buffer Store
            bytes_remaining = self.sat_images.image_1_size
            send_bytes = open(image_1_str,'rb')
            # Loop through image and store contents in an array
            while (bytes_remaining > 0):
                if (bytes_remaining >= 128):
                    self.image_array.append(send_bytes.read(128))
                else:
                    self.image_array.append(send_bytes.read(bytes_remaining))
                    
                bytes_remaining -= 128
            # Close file when complete
            send_bytes.close()

    '''
        Name: unpack_message
        Description: Unpack message based on its ID
        Inputs:
            packet - Data received from RFM module
    '''
    def unpack_message(self,packet):
        # Can run deconstruct_message() for debug output 
        self.rx_message_ID = int.from_bytes(packet[0:1],'big')
        self.rx_message_sequence_count = int.from_bytes(packet[1:3],'big')
        self.rx_message_size = int.from_bytes(packet[3:4],'big')
        print("Message received header:",list(packet[0:4]))

        if (self.rx_message_ID == GS_ACK):
            self.gs_rx_message_ID = int.from_bytes(packet[4:5],'big')
            self.gs_req_message_ID = int.from_bytes(packet[5:6],'big')
            self.gs_req_seq_count = int.from_bytes(packet[6:8],'big')

    '''
        Name: received_message
        Description: This function waits for a message to be received from the LoRa module
    '''
    def receive_message(self):
        received_success = False
        wait_time = 0
        begin_time = time.time()

        while not received_success:
            my_packet = cubesat.radio1.receive()
            if my_packet is None:
                wait_time = time.time() - begin_time
                if (wait_time >= 5):
                    self.heartbeat_sent = False
                    break
            else:
                print(f'Received (raw bytes): {my_packet}')
                rssi = cubesat.radio1.rssi(raw=True)
                print(f'Received signal strength: {rssi} dBm')
                self.unpack_message(my_packet)
                received_success = True

    '''
        Name: transmit_message
        Description: SAT transmits message via the LoRa module when the function is called.
    '''
    def transmit_message(self):
        send_multiple = True
        multiple_packet_count = 0

        while send_multiple:
            time.sleep(0.15)

            if not self.heartbeat_sent:
                # Transmit SAT heartbeat
                tx_message = construct_message(SAT_HEARTBEAT)
                self.heartbeat_sent = True

            elif self.gs_req_message_ID == SAT_IMAGES:
                # Transmit stored image info
                tx_header = bytes([SAT_IMAGES,0x0,0x0,0x18])
                tx_payload = self.image_pack_info()
                tx_message = tx_header + tx_payload

            elif self.gs_req_message_ID == SAT_DEL_IMG1:
                # Transmit successful deletion of stored image 1
                tx_header = bytes([SAT_DEL_IMG1,0x0,0x0,0x1])
                tx_payload = bytes([0x1])
                tx_message = tx_header + tx_payload
                self.image_deleted = True
            
            elif self.gs_req_message_ID == SAT_DEL_IMG2:
                # Transmit successful deletion of stored image 2
                tx_header = bytes([SAT_DEL_IMG2,0x0,0x0,0x1])
                tx_payload = bytes([0x1])
                tx_message = tx_header + tx_payload
                self.image_deleted = True

            elif self.gs_req_message_ID == SAT_DEL_IMG3:
                # Transmit successful deletion of stored image 3
                tx_header = bytes([SAT_DEL_IMG3,0x0,0x0,0x1])
                tx_payload = bytes([0x1])
                tx_message = tx_header + tx_payload
                self.image_deleted = True

            elif (self.gs_req_message_ID == SAT_IMG1_CMD) or (self.gs_req_message_ID == SAT_IMG2_CMD) or (self.gs_req_message_ID == SAT_IMG3_CMD):
                # Transmit image in multiple packets
                if (self.gs_req_message_ID != self.last_image_id) or (self.image_deleted):
                    self.image_pack_images(self.gs_req_message_ID)
                    self.image_deleted = False

                # Header
                tx_header = (self.gs_req_message_ID.to_bytes(1,'big') + self.gs_req_seq_count.to_bytes(2,'big') \
                            + len(self.image_array[self.gs_req_seq_count]).to_bytes(1,'big'))
                # Payload
                tx_payload = self.image_array[self.gs_req_seq_count + multiple_packet_count]
                # Pack entire message
                tx_message = tx_header + tx_payload
                # Set last image tracker
                self.last_image_id = self.gs_req_message_ID

            else:
                # Run construct_message() when telemetry information is complete
                tx_header = (self.gs_req_message_ID.to_bytes(1,'big') + (0x0).to_bytes(1,'big') + (0x0).to_bytes(1,'big') + (0x0).to_bytes(1,'big'))
                tx_message = tx_header

            # Send a message to GS
            cubesat.radio1.send(tx_message)

            # This code is practically the same as Ground Station function hold_receive_mode
            if ((self.gs_req_message_ID == SAT_IMG1_CMD) or (self.gs_req_message_ID == SAT_IMG2_CMD) or (self.gs_req_message_ID == SAT_IMG3_CMD)):
                if (self.gs_req_message_ID == SAT_IMG2_CMD):
                    target_sequence_count = self.sat_images.image_2_message_count
                elif (self.gs_req_message_ID == SAT_IMG3_CMD):
                    target_sequence_count = self.sat_images.image_3_message_count
                else:
                    target_sequence_count = self.sat_images.image_1_message_count
                
                if (((((self.gs_req_seq_count + multiple_packet_count) % self.send_mod) > 0) and ((self.gs_req_message_ID + multiple_packet_count) < (target_sequence_count - 1))) or \
                    ((self.gs_req_seq_count + multiple_packet_count) == 0)):
                    multiple_packet_count += 1
                    send_multiple = True
                else:
                    send_multiple = False
            else:
                send_multiple = False

            # Debug output of message in bytes
            print("Satellite sent message:", tx_message)
            print("\n")