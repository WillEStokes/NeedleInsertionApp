import socket
import struct
import time
import csv
from PyQt6.QtCore import QThread, pyqtSignal

IP_ADDRESS = "192.168.5.101"
TCP_PORT = 7851

FID_GET_STATUS = 0
FID_GET_SYSTEM_INFO = 1
FID_GET_FT_SENSOR_DATA = 2
FID_GET_ENCODER_SENSOR_DATA = 3
FID_GET_ALL_SENSOR_DATA = 4
FID_START_ACQUISITION_STREAM = 5
FID_STOP_ACQUISITION_STREAM = 6
FID_RESET_ADC = 7
FID_CHECK_ADC = 8
FID_SET_ADC_CONVERSION_MODE = 9

CALIBRATION_MATRIX = [[0.00135, -0.04604, 0.02344, -3.22662, -0.00322, 3.17008],
                     [-0.00694, 4.16569, 0.02971, -1.87643, 0.02738, -1.79608],
                     [3.69182, 0.02713, 3.83425, -0.03329, 3.65801, -0.067],
                     [0.15408, 25.37956, 21.34115, -11.71178, -20.50426, -10.51265],
                     [-23.9405, 0.07684, 12.2178, 19.58172, 12.22442, -19.60731],
                     [0.09832, 17.49271, -0.32435, 15.76607, -0.09154, 15.24495]]

class DataStream(QThread):
    data_received = pyqtSignal(tuple)

    def __init__(self, socket):
        super().__init__()
        self.socket = socket
        self.stopped = False
        self.logging_flag = False
        self.csv_file = None
        self.sequence_name = None
        self.time = 0
        self.start_time = 0
        self.all_data = tuple([0] * 9)
        self.data_offset = tuple([0] * 9)

    def set_logging_flag(self, flag):
        self.logging_flag = flag

    def set_sequence_name(self, sequence_name):
        self.sequence_name = sequence_name

    def set_data_offset(self):
        self.data_offset = self.all_data

    def calibration_transform(self, tuple_values):
        result = [0] * 6
        
        for i in range(6):
            for j in range(6):
                result[i] += CALIBRATION_MATRIX[i][j] * tuple_values[j]
        
        return tuple(result)

    def initialise_csv(self):
        formatted_time = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
        self.csv_file = open(f"output/{self.sequence_name}_{formatted_time}.csv", "w", newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(['time', 'fx', 'fy', 'fz', 'tx', 'ty', 'tz', 'px', 'py', 'pz'])
        self.start_time = self.time

    def close_csv(self):
        self.csv_file.close()
        self.csv_file = None

    def run(self):
        all_data_size = struct.calcsize('<ffffffffff')
        csv_initialised = False
        while not self.stopped:
            try:
                data = self.socket.recv(all_data_size)
                if not data:
                    break

                self.time = struct.unpack('<I', data[:4])[0]
                ft_data = struct.unpack('<ffffff', data[4:28])
                encoder_data = struct.unpack('<fff', data[28:])

                calibrated_ft_data = self.calibration_transform(ft_data)

                self.all_data = calibrated_ft_data + encoder_data
                adjusted_data = tuple(x - offset for x, offset in zip(self.all_data, self.data_offset))

                self.data_received.emit(adjusted_data) # Emit all 9 channels of data to the Display class

                if self.logging_flag:
                    if not csv_initialised:
                        self.initialise_csv()
                        csv_initialised = True
                    # self.time += 0.005
                    self.csv_writer.writerow([self.time - self.start_time] + list(adjusted_data))
                else:
                    if self.csv_file is not None:
                        self.close_csv()
                        csv_initialised = False

            except Exception as e:
                print(f"Error reading data from the Ethernet device: {e}")
                break

    def stop(self):
        self.stopped = True

class K64F:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.connected = False
        self.data_stream = None

    def init_ethernet(self):
        # i = 1 # do something
        try:
            self.socket.connect((IP_ADDRESS, TCP_PORT))
            self.connected = True
            print("Connected to Ethernet device.")
        except Exception as e:
            print(f"Error connecting to Ethernet device: {e}")
            self.connected = False

    def start_data_stream(self):
        self.data_stream = DataStream(self.socket)
        self.data_stream.start()

    def stop_data_stream(self):
        if self.data_stream:
            self.data_stream.stop()

    def invoke_fid(self, fid):
        packet_length = 4
        error = 0
        message_header = struct.pack('<HBB', packet_length, fid, error)
        self.socket.sendall(message_header)

    def start_acquisition(self):
        if not self.connected:
            print("Not connected to the Ethernet device.")
            return

        self.invoke_fid(FID_START_ACQUISITION_STREAM)

        print("Start acquisition message sent.")
        self.start_data_stream()

    def stop_acquisition(self):
        if not self.connected:
            print("Not connected to the Ethernet device.")
            return

        self.invoke_fid(FID_STOP_ACQUISITION_STREAM)

        print("Stop acquisition message sent.")
        self.stop_data_stream()

    def enable_logging(self):
        if self.data_stream:
            self.data_stream.set_logging_flag(True)

    def disable_logging(self):
        if self.data_stream:
            self.data_stream.set_logging_flag(False)

    def set_sequence_name(self, sequence_name):
        self.data_stream.set_sequence_name(sequence_name)

    def set_data_offset(self):
        self.data_stream.set_data_offset()

    def close(self):
        if self.connected:
            self.socket.close()
            self.connected = False
            print("Connection to Ethernet device closed.")