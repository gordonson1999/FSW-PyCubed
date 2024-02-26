"""
Onboard Mass Storage System (SD Card) Interface
======================
Python package to interface with the onboard mass storage system (SD Card). 
It is the single point of access to the SD Card for the flight software.

Author: Ibrahima Sory Sow
"""

import sys
import os
import struct
import time

from storage import mount, VfsFat
import sdcardio

from micropython import const


_CLOSED = const(20)
_OPEN = const(21)


_FORMAT = {
            'b': 1,
            'B': 1,
            'h': 2,
            'H': 2,
            'i': 4,
            'I': 4,
            'l': 4,
            'L': 4,
            'q': 8,
            'Q': 8,
            'f': 4,
            'd': 8
        }



class FileManager:
    """
    Managing class for the SD Card.


    Note: If the same SPI bus is shared with other peripherals, the SD card must be initialized before accessing any other peripheral on the bus. 
    Failure to do so can prevent the SD card from being recognized until it is powered off or re-inserted.       
    """


    def __init__(self, spi_bus, board_pin, baudrate=4000000):

        self.sd_path = "/sd"
        try:
            _sd = sdcardio.SDCard(spi_bus, board_pin, baudrate=4000000)
            _vfs = VfsFat(_sd)
            mount(_vfs, self.sd_path)
            sys.path.append(self.sd_path)
            self.fs=_vfs
        except Exception as e:
            print('[ERROR][SD Card]', e)

        # Keep track of all file processes
        self.file_process_registry = dict()
        # TODO Scan the SD card to register existing file processes


    def list_directories(self):
        return os.listdir(self.sd_path)


    def register_file_process(self, tag_name, data_format, line_limit=1000):
        self.file_process_registry[tag_name] = FileProcess(tag_name, data_format, line_limit=line_limit)

    # DEBUG ONLY
    def get_file_process(self, tag_name):
        return self.file_process_registry[tag_name]
    
    def get_all_file_processes_name(self):
        return self.file_process_registry.keys()
    
    # DEBUG ONLY
    def get_all_file_processes(self):
        return self.file_process_registry.values()
    
    def get_storage_info(self, tag_name):
        try:
            if tag_name in self.file_process_registry:
                self.file_process_registry[tag_name].get_storage_info()
            else:
                raise KeyError("File process not registered.")
        except KeyError as e:
            print(f"Error: {e}")

    def request_tm_file(self, tag_name):
        """
        Returns the path of a designated file available for transmission. 
        If no file is available, the function returns None.

        The function store the file path to be excluded in clean-up policies. Once fully transmitted, notify_tm_file() must be called to remove the file from the exclusion list.
        """
        try:
            if tag_name in self.file_process_registry:
                return self.file_process_registry[tag_name].request_tm_file()
            else:
                raise KeyError("File process not registered!")
        except KeyError as e:
            print(f"Error: {e}")
    
    def notify_tm_file(self, tag_name): 
        """
        Acknowledge the transmission of the file. 
        The file is then removed from the exclusion list.
        """
        try:
            if tag_name in self.file_process_registry:
                self.file_process_registry[tag_name].notify_tm_file()
            else:
                raise KeyError("File process not registered!")
        except KeyError as e:
            print(f"Error: {e}")


    def log_data(self, tag_name, *data):
        # Must check if tag_name is in the registry
        try:
            if tag_name in self.file_process_registry:
                self.file_process_registry[tag_name].add(*data)
            else:
                raise KeyError("File process not registered!")
        except KeyError as e:
            print(f"Error: {e}")


    def delete_all_files(self, path="/sd"):
        try:
            for file_name in os.listdir(path):
                file_path = path + '/' + file_name
                if os.stat(file_path)[0] & 0x8000:  # Check if file is a regular file
                    os.remove(file_path)
                elif os.stat(file_path)[0] & 0x4000:  # Check if file is a directory
                    self.delete_all_files(file_path)  # Recursively delete files in subdirectories
                    os.rmdir(file_path)  # Delete the empty directory
            print("All files and directories deleted successfully!")
        except Exception as e:
            print(f"Error deleting files and directories: {e}")

    def get_current_file_size(self, tag_name):
        try:
            if tag_name in self.file_process_registry:
                return self.file_process_registry[tag_name].get_current_file_size()
            else:
                raise KeyError("File process not registered!")
        except KeyError as e:
            print(f"Error: {e}")

            
    # DEBUG ONLY
    def print_directory(self, path="/sd", tabs=0):
        for file in os.listdir(path):
            stats = os.stat(path + "/" + file)
            filesize = stats[6]
            isdir = stats[0] & 0x4000

            if filesize < 1000:
                sizestr = str(filesize) + " by"
            elif filesize < 1000000:
                sizestr = "%0.1f KB" % (filesize / 1000)
            else:
                sizestr = "%0.1f MB" % (filesize / 1000000)
            printname = ""
            for _ in range(tabs):
                printname += "   "
            printname += file
            if isdir:
                printname += "/"
            print('{0:<40} Size: {1:>10}'.format(printname, sizestr))
            # recursively print directory contents
            if isdir:
                self.print_directory(path + "/" + file, tabs + 1)



class FileProcess:
    """
    Class for managing a single logging stream.

    Attributes: TODO
        tag_name (str): The tag name for the file.
        data_format (str): The format of the data to be written to the file.
        home_path (str): The home path for the file (default is "/sd/").
        status (str): The status of the file ("CLOSED" or "OPEN").
        file (file): The file object.
        dir_path (str): The directory path for the file.
        current_filename (str): The current filename.
        bytesize (int): The size of each new data line to be written to the file.
    """
    
    def __init__(self, tag_name, data_format, line_limit=1000, home_path="/sd") -> None:
        """
        Args:
            tag_name (str): The tag name for the file (with no spaces or special characters)
            data_format (str): The format of the data to be written to the file. e.g. 'iff', 'iif', 'fff', 'iii', etc
            home_path (str, optional): The home path for the file (default is "/sd/").
        """
        self.status = _CLOSED

        self.tag_name = tag_name
        self.file = None
        self.dir_path = home_path + '/' + tag_name + '/'
        self.create_folder()
        self.current_filename = self.create_new_filename()

        # TODO Check formating e.g. 'iff', 'iif', 'fff', 'iii', etc. ~ done within compute_bytesize()
        self.data_format = '<' +  data_format # Need to specify endianness to disable padding (https://stackoverflow.com/questions/47750056/python-struct-unpack-length-error/47750278#47750278)
        self.bytesize = self.compute_bytesize(self.data_format)

        # TODO To Be Resolved for each file process, TODO check if int
        self.size_limit = line_limit * self.bytesize  # Default size limit is 1000 data lines


        self.tm_filename = None


    def create_folder(self):
        if not path_exist(self.dir_path):
            try:
                os.mkdir(self.dir_path)
                print("Folder created successfully.")
            except OSError as e:
                print(f"Error creating folder: {e}")
        else:
            print("Folder already exists.")


    def create_new_filename(self):
        # TODO timestamp must be obtained through the REFERENCE TIME
        return self.dir_path + self.tag_name + '_' + str(time.time()) + '.bin'


    def compute_bytesize(self, data_format):
        """
        Compute the bytesize for each new data line to be written to the file.
        """
        b_size = 0
        for c in data_format[1:]: # do not include the endianness character
            if c not in _FORMAT:
                raise ValueError(f"Invalid format character '{c}'")
            b_size += _FORMAT[c]
        return b_size


    def resolve_current_file(self):
        """
        Resolve the current file to write to.
        """
        if self.status == _CLOSED:
            self.current_filename = self.create_new_filename()
            self.open()
        elif self.status == _OPEN:
            current_file_size = self.get_current_file_size()
            if current_file_size >= self.size_limit:
                self.close()
                self.current_filename = self.create_new_filename()
                self.open()


    def open(self):
        if self.status == _CLOSED:
            self.file = open(self.current_filename, "ab")
            self.status = _OPEN
        else:
            print("File is already open.")

    def close(self):
        if self.status == _OPEN:
            self.file.close()
            self.status = _CLOSED
        else:
            print("File is already closed.")


    def get_storage_info(self):
        """
        Returns storage information for the current file process which includes:
        - Number of files 
        - Total directory size 
        - ... TODO

        Returns:
            A tuple containing all storage information.
        """
        files = os.listdir(self.dir_path)
        total_size = len(files[:-1]) * self.size_limit + self.get_current_file_size()
        return len(files), total_size


    def get_current_file_size(self):
        file_path = self.current_filename
        try:
            file_stats = os.stat(file_path)
            filesize = file_stats[6] # size of the file in bytes
            return filesize
        except OSError as e:
            print(f"Error getting file size: {e}")
            return None

    
    def add(self, *data): 
        self.resolve_current_file()

        bin_data = struct.pack(self.data_format, *data)
        self.file.write(bin_data)
        self.file.flush() # Flush immediately 

    def request_tm_file(self):
        """
        Returns the path of a designated file available for transmission. 
        If no file is available, the function returns None.

        The function store the file path to be excluded in clean-up policies. Once fully transmitted, notify_tm_file() must be called to remove the file from the exclusion list.
        """
        # Assumes correct ordering (monotonic timestamp)
        # TODO
        files = os.listdir(self.dir_path)
        if len(files) > 0:
            self.tm_filename = self.dir_path + files[0]
            if self.tm_filename == self.current_filename:
                self.close()
            return self.tm_filename
        else:
            return None

    def notify_tm_file(self): 
        """
        Acknowledge the transmission of the file. 
        The file is then removed from the exclusion list.
        """
        # TODO
        if self.tm_filename:
            os.remove(self.tm_filename)
            self.tm_filename = None
        else:
            print("No file to acknowledge.")


    # DEBUG ONLY
    def read_current_file(self):
        self.close()
        if self.status == _CLOSED:
            # TODO file not existing
            with open(self.current_filename, "rb") as file:
                content = []
                # TODO add max iter (max lines to read from file)
                while True:
                    cr = file.read(self.bytesize)
                    if not cr:
                        break
                    content.append(struct.unpack(self.data_format, cr))
                return content
        else:
            print("File is not closed!")




def path_exist(filename):
    """
    Replacement for os.path.exists() function, which is not implemented in micropython.
    """
    try:
        os.stat(filename)
        #print("Path exists!")
        return True
    except OSError:
        #print("Path does not exist!")
        return False

    
    

