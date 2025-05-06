import csv
from datetime import datetime
import os
import serial

class DataLogger:
    def __init__(self, serial_port='COM3', baudrate=9600, csv_file='pulse_data.csv'):
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.csv_file = csv_file
        self.ser = None
        self._initialize_csv()

    def _initialize_csv(self):
        """Create CSV file with headers if it doesn't exist"""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'signal', 'bpm', 'beat_detected'])

    def connect_serial(self):
        """Establish serial connection"""
        try:
            self.ser = serial.Serial(self.serial_port, self.baudrate, timeout=1)
            print(f"Connected to {self.serial_port}")
            return True
        except Exception as e:
            print(f"Serial connection error: {e}")
            return False

    def log_data(self):
        """Read serial data and log to CSV"""
        try:
            while True:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8').strip()
                    
                    if line.startswith('DATA:'):
                        data = line[5:].split(',')
                        timestamp, signal, bpm, beat_flag = data
                        
                        with open(self.csv_file, 'a', newline='') as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                datetime.now().isoformat(),
                                signal,
                                bpm,
                                bool(int(beat_flag))
                            ])
                        
                        yield {  # For real-time updates
                            'timestamp': datetime.now().isoformat(),
                            'signal': int(signal),
                            'bpm': int(bpm),
                            'beat': bool(int(beat_flag))
                        }

        except KeyboardInterrupt:
            print("Logging stopped")
        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()

if __name__ == "__main__":
    logger = DataLogger()
    if logger.connect_serial():
        for data in logger.log_data():
            print(data)  # Simple console output

