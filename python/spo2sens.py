import serial

class Spo2Sensor:
    def __init__(self, port, baudrate=115200):
        self.serial = serial.Serial(port, baudrate, timeout=1)
    
    def read_data(self):
        line = self.serial.readline().decode('utf-8').strip()
        if line.startswith("HR:"):
            return int(line.split(":")[1])  # Example: "HR:72" → 72
        return None