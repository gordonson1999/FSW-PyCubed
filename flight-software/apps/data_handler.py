"""
Onboard Data Handling (OBDH) Module 

======================

This module provides the main interface for the onboard data handling system consisting of:
- Persistent storage management and single point of access for the onboard mass storage system (SD Card)
- Logging interface for flight software tasks
- Automated file services for the flight software, including telemetry (TM) and telecommand (TC) file generation for transmission
- Data processing and formatting for the flight software

Author: Ibrahima Sory Sow
"""

import os
import re
import struct
import time
import json


from storage import mount, VfsFat
import sdcardio

from micropython import const


_CLOSED = const(20)
_OPEN = const(21)


_FORMAT = {
            'b': 1,   # byte
            'B': 1,   # unsigned byte
            'h': 2,   # short
            'H': 2,   # unsigned short
            'i': 4,   # int
            'I': 4,   # unsigned int
            'l': 4,   # long
            'L': 4,   # unsigned long
            'q': 8,   # long long
            'Q': 8,   # unsigned long long
            'f': 4,   # float
            'd': 8    # double
        }


_PROCESS_CONFIG_FILENAME = ".process_configuration.json"

from collections import OrderedDict




class DataHandler:
    """
    Managing class for the SD Card.


    Note: If the same SPI bus is shared with other peripherals, the SD card must be initialized before accessing any other peripheral on the bus. 
    Failure to do so can prevent the SD card from being recognized until it is powered off or re-inserted.       
    """

    sd_path = "/sd"
    # Keep track of all file processes
    data_process_registry = dict()

    @classmethod
    def scan_SD_card(cls):
        """
        Scans the SD card for configuration files and registers data processes.

        This method scans the SD card for directories and checks if each directory contains a configuration file.
        If a configuration file is found, it reads the data format and line limit from the file and registers
        a data process with the specified parameters.

        Returns:
            None

        Example:
            DataHandler.scan_SD_card()
        """
        directories = cls.list_directories()
        print(directories)
        for dir_name in directories:
            config_file = join_path(cls.sd_path, dir_name, _PROCESS_CONFIG_FILENAME)
            if path_exist(config_file):
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                    data_format = config_data['data_format']
                    line_limit = config_data['line_limit']
                    if data_format and line_limit:
                        cls.register_data_process(dir_name, data_format, persistent=True, line_limit=line_limit)

        # print("SD Card Scanning complete - found ", cls.data_process_registry.keys())


    @classmethod
    def register_data_process(cls, tag_name, data_format, persistent, line_limit=1000):
        """
        Register a data process with the given parameters.

        Parameters:
        - tag_name (str): The name of the data process.
        - data_format (str): The format of the data.
        - persistent (bool): Whether the data should be logged to a file.
        - line_limit (int, optional): The maximum number of data lines to store. Defaults to 1000.

        Raises:
        - ValueError: If line_limit is not a positive integer.

        Returns:
        - None
        """
        if isinstance(line_limit, int) and line_limit > 0:
            cls.data_process_registry[tag_name] = DataProcess(tag_name, data_format, persistent=persistent, line_limit=line_limit)
        else:
            raise ValueError("Line limit must be a positive integer.")


    @classmethod
    def log_data(cls, tag_name, *data):
        """
        Logs the provided data using the specified tag name.

        Parameters:
        - tag_name (str): The name of data process to associate with the logged data.
        - *data: The data to be logged.

        Raises:
        - KeyError: If the provided tag name is not registered in the data process registry.

        Returns:
        - None
        """
        try:
            if tag_name in cls.data_process_registry:
                cls.data_process_registry[tag_name].log(*data)
            else:
                raise KeyError("Data process not registered!")
        except KeyError as e:
            print(f"Error: {e}")

    @classmethod
    def get_latest_data(cls, tag_name):
        """
        Returns the latest data point for the specified data process.

        Parameters:
        - tag_name (str): The name of the data process.

        Raises:
        - KeyError: If the provided tag name is not registered in the data process registry.

        Returns:
        - The latest data point for the specified data process.
        """
        try:
            if tag_name in cls.data_process_registry:
                return cls.data_process_registry[tag_name].get_latest_data()
            else:
                raise KeyError("Data process not registered!")
        except KeyError as e:
            print(f"Error: {e}")


    @classmethod
    def list_directories(cls):
        return os.listdir(cls.sd_path)


    # DEBUG ONLY
    @classmethod
    def get_data_process(cls, tag_name):
        return cls.data_process_registry[tag_name]
    
    @classmethod
    def get_all_data_processes_name(cls):
        return cls.data_process_registry.keys()
    
    # DEBUG ONLY
    @classmethod
    def get_all_data_processes(cls):
        return cls.data_process_registry.values()
    
    @classmethod
    def get_storage_info(cls, tag_name):
        try:
            if tag_name in cls.data_process_registry:
                cls.data_process_registry[tag_name].get_storage_info()
            else:
                raise KeyError("File process not registered.")
        except KeyError as e:
            print(f"Error: {e}")

    @classmethod
    def request_TM_path(cls, tag_name, latest=False):
        """
        Returns the path of a designated file available for transmission. 
        If no file is available, the function returns None.

        The function store the file path to be excluded in clean-up policies. 
        Once fully transmitted, notify_TM_path() must be called to remove the file from the exclusion list.
        """
        try:
            if tag_name in cls.data_process_registry:
                return cls.data_process_registry[tag_name].request_TM_path(latest=latest)
            else:
                raise KeyError("Data  process not registered!")
        except KeyError as e:
            print(f"Error: {e}")
    
    @classmethod
    def notify_TM_path(cls, tag_name, path): 
        """
        Acknowledge the transmission of the file. 
        The file is then removed from the exclusion list.
        """
        try:
            if tag_name in cls.data_process_registry:
                cls.data_process_registry[tag_name].notify_TM_path(path)
            else:
                raise KeyError("Data process not registered!")
        except KeyError as e:
            print(f"Error: {e}")

    @classmethod
    def clean_up(cls):
        """
        Clean up the files that have been transmitted and acknowledged.
        """
        for tag_name in cls.data_process_registry:
            cls.data_process_registry[tag_name].clean_up()


    @classmethod
    def delete_all_files(cls, path="/sd"):
        try:
            for file_name in os.listdir(path):
                file_path = path + '/' + file_name
                if os.stat(file_path)[0] & 0x8000:  # Check if file is a regular file
                    os.remove(file_path)
                elif os.stat(file_path)[0] & 0x4000:  # Check if file is a directory
                    cls.delete_all_files(file_path)  # Recursively delete files in subdirectories
                    os.rmdir(file_path)  # Delete the empty directory
            print("All files and directories deleted successfully!")
        except Exception as e:
            print(f"Error deleting files and directories: {e}")

    @classmethod
    def get_current_file_size(cls, tag_name):
        try:
            if tag_name in cls.data_process_registry:
                return cls.data_process_registry[tag_name].get_current_file_size()
            else:
                raise KeyError("File process not registered!")
        except KeyError as e:
            print(f"Error: {e}")

            
    # DEBUG ONLY
    @classmethod
    def print_directory(cls, path="/sd", tabs=0):
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
                cls.print_directory(path + "/" + file, tabs + 1)



class DataProcess:
    """
    Class for managing a single logging stream.

    Attributes:
        tag_name (str): The tag name for the file.
        data_format (str): The format of the data to be written to the file.
        persistent (bool): Whether the data should be logged to a file (default is True).
        home_path (str): The home path for the file (default is "/sd/").
        status (str): The status of the file ("CLOSED" or "OPEN").
        file (file): The file object.
        dir_path (str): The directory path for the file.
        current_path (str): The current filename.
        bytesize (int): The size of each new data line to be written to the file.
    """

    def __init__(self, tag_name, data_format, persistent=True, line_limit=1000, new_config_file=False, home_path="/sd") -> None:
            """
            Initializes a DataProcess object.

            Args:
                tag_name (str): The tag name for the file (with no spaces or special characters)
                data_format (str): The format of the data to be written to the file. e.g. 'iff', 'iif', 'fff', 'iii', etc
                persistent (bool, optional): Whether the file should be persistent or not (default is True).
                line_limit (int, optional): The maximum number of data lines allowed in the file (default is 1000).
                home_path (str, optional): The home path for the file (default is "/sd/").
            """

            self.tag_name = tag_name
            self.file = None
            self.persistent = persistent

            # TODO Check formating e.g. 'iff', 'iif', 'fff', 'iii', etc. ~ done within compute_bytesize()
            self.data_format = '<' +  data_format # Need to specify endianness to disable padding (https://stackoverflow.com/questions/47750056/python-struct-unpack-length-error/47750278#47750278)
            self.bytesize = self.compute_bytesize(self.data_format)

            self.last_data = {}


            if self.persistent:

                self.status = _CLOSED

                self.dir_path = home_path + '/' + tag_name + '/'
                self.create_folder()

                # To Be Resolved for each file process, TODO check if int, positive, etc
                self.size_limit = line_limit * self.bytesize  # Default size limit is 1000 data lines

                self.current_path = self.create_new_path()

                self.delete_paths = [] # Paths that are flagged for deletion
                self.excluded_paths = [] # Paths that are currently being transmitted

                config_file_path = self.dir_path + _PROCESS_CONFIG_FILENAME
                if not path_exist(config_file_path) or new_config_file:
                    config_data = {
                        'data_format': self.data_format[1:], # remove the < character
                        'line_limit': line_limit
                    }
                    with open(config_file_path, 'w') as config_file:
                        json.dump(config_data, config_file)


    def create_folder(self):
        if not path_exist(self.dir_path):
            try:
                os.mkdir(self.dir_path)
                print("Folder created successfully.")
            except OSError as e:
                print(f"Error creating folder: {e}")
        else:
            # TODO log
            print("Folder already exists.")


        


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


    def log(self, *data): 
        """
        Logs the given data (eventually to a file if persistent = True).

        Args:
            *data: Variable number of data values to be logged in an OrderedDict.

        Returns:
            None
        """
        self.resolve_current_file()
        self.last_data = data

        if self.persistent:
            bin_data = struct.pack(self.data_format, *data)
            self.file.write(bin_data)
            self.file.flush() # Flush immediately


    def get_latest_data(self):
            """
            Returns the latest data point.

            If a data point has been logged, it returns the last data point.
            If no data point has been logged yet, it returns None.

            Returns:
                The latest data point or None if no data point has been logged yet.
            """
            if self.last_data is not None:
                return self.last_data
            else:
                # TODO handle case where no data has been logged yet?
                return None
                #raise ValueError("No latest data point available.")


    def resolve_current_file(self):
        """
        Resolve the current file to write to.
        """
        if self.status == _CLOSED:
            self.current_path = self.create_new_path()
            self.open()
        elif self.status == _OPEN:
            current_file_size = self.get_current_file_size()
            if current_file_size >= self.size_limit:
                self.close()
                self.current_path = self.create_new_path()
                self.open()


    def create_new_path(self):
        # TODO timestamp must be obtained through the REFERENCE TIME until the time module is done
        return self.dir_path + self.tag_name + '_' + str(time.time()) + '.bin'

    def open(self):
        if self.status == _CLOSED:
            self.file = open(self.current_path, "ab+")
            self.status = _OPEN
        else:
            print("File is already open.")

    def close(self):
        if self.status == _OPEN:
            self.file.close()
            self.status = _CLOSED
        else:
            print("File is already closed.")


    def request_TM_path(self, latest=False):
        """
        Returns the path of a designated file available for transmission. 
        If no file is available, the function returns None.

        The function store the file path to be excluded in clean-up policies. 
        Once fully transmitted, notify_TM_path() must be called to remove the file from the exclusion list.
        """
        # Assumes correct ordering (monotonic timestamp)
        # TODO
        files = os.listdir(self.dir_path)
        if len(files) > 1: # Ignore process configuration file

            if latest:
                transmit_file = files[-1]
                if transmit_file == _PROCESS_CONFIG_FILENAME:
                    transmit_file = files[-2]
            else:
                transmit_file = files[0]
                if transmit_file == _PROCESS_CONFIG_FILENAME:
                    transmit_file = files[1]
                
            tm_path = self.dir_path + transmit_file

            if tm_path == self.current_path:
                self.close()
                self.resolve_current_file()

            self.excluded_paths.append(tm_path)
            return tm_path
        else:
            return None


    def notify_TM_path(self, path): 
        """
        Acknowledge the transmission of the file. 
        The file is then removed from the excluded list and added to the deletion list.
        """
        if path in self.excluded_paths:
            self.excluded_paths.remove(path)
            self.delete_paths.append(path) 
            # TODO handle case where comms transmitted a file it wasn't suposed to? 
        else:
            # TODO log
            print("No file to acknowledge.")


    def clean_up(self):
        """
        Clean up the files that have been transmitted and acknowledged.
        """
        for d_path in self.delete_paths:
            if path_exist(d_path):
                os.remove(d_path)
            else:
                # TODO - log error, use exception handling instead
                print(f"File {d_path} does not exist.")

            self.delete_paths.remove(d_path)
        

    def get_storage_info(self):
        """
        Returns storage information for the current file process which includes:
        - Number of files in the directory
        - Total directory size in bytes
        - TODO

        Returns:
            A tuple containing the number of files and the total directory size.
        """
        files = os.listdir(self.dir_path)
        total_size = len(files) * self.size_limit + self.get_current_file_size()
        return len(files), total_size


    def get_current_file_size(self):
        
        if path_exist(self.current_path):
            try:
                file_stats = os.stat(self.current_path)
                filesize = file_stats[6] # size of the file in bytes
                return filesize
            except OSError as e:
                # TODO log
                print(f"Error getting file size: {e}")
                return None
        else:
            # TODO handle case where file does not exist
            print("File does not exist.")
            return None

    

    # DEBUG ONLY
    def read_current_file(self):
        self.close()
        if self.status == _CLOSED:
            # TODO file not existing
            with open(self.current_path, "rb") as file:
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


class ImageProcess:
    pass



def path_exist(path):
    """
    Replacement for os.path.exists() function, which is not implemented in micropython. If the request if for a directory, the function will return True if the directory exists, even if it is empty.
    """
    try_path = path
    if path[-1] == '/':
        try_path = path[:-1]

    try:
        os.stat(try_path)
        return True
    except OSError as e:
        print(f"Error: {e}")
        return False

def join_path(*paths):
    """
    Join multiple paths together into a single path.

    Args:
        *paths: Variable number of paths to be joined.

    Returns:
        The joined path.
    """
    return re.sub(r'/+', '/', '/'.join(paths))