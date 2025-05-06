import tkinter as tk
from tkinter import ttk
import serial
import threading
import queue
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class SensorMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sensor Data Monitor")
        self.root.geometry("1400x1000")  # Increased height to accommodate the plot
        
        # Serial configuration
        self.serial_port = 'COM6'  # Change to your port
        self.baudrate = 115200
        self.ser = None
        self.running = False
        self.data_queue = queue.Queue()
        
        # ECG data storage
        self.ecg_data = []
        self.max_ecg_points = 500  # Number of ECG points to display
        
        # Data headers with added "Signal" column
        self.headers = [
            "Timestamp", 
            "Ambient Temp (°C)", 
            "Body Temp (°C)", 
            "Pressure (hPa)", 
            "Depth (m)", 
            "Water Temp (°C)", 
            "ECG Values", 
            "BPM", 
            "Signal",
            "Deco Message"
        ]
        
        # Create GUI
        self.create_widgets()
        
        # Start serial thread
        self.start_serial_thread()

    def create_widgets(self):
        """Create all GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title label
        title_label = ttk.Label(main_frame, text="Sensor Data Monitor", font=('Helvetica', 16))
        title_label.pack(pady=10)
        
        # Control buttons frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(control_frame, text="Start", command=self.start_monitoring).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Stop", command=self.stop_monitoring).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Clear", command=self.clear_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Exit", command=self.on_closing).pack(side=tk.RIGHT, padx=5)
        
        # Status label
        self.status_var = tk.StringVar(value="Status: Not connected")
        status_label = ttk.Label(control_frame, textvariable=self.status_var)
        status_label.pack(side=tk.RIGHT, padx=20)
        
        # Create a frame for the table and plot
        display_frame = ttk.Frame(main_frame)
        display_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview widget for tabular data display
        self.tree = ttk.Treeview(display_frame, columns=self.headers, show="headings", selectmode="browse")
        
        # Configure columns
        for col in self.headers:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor=tk.CENTER)
        
        # Adjust specific column widths
        self.tree.column("Timestamp", width=150)
        self.tree.column("ECG Values", width=150)
        self.tree.column("Signal", width=150)
        self.tree.column("Deco Message", width=200)
        
        # Add scrollbars to the table
        scroll_y = ttk.Scrollbar(display_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scroll_x = ttk.Scrollbar(display_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        # Grid layout for the table
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        
        # Configure grid weights
        display_frame.grid_rowconfigure(0, weight=1)
        display_frame.grid_columnconfigure(0, weight=1)
        
        # Create ECG plot frame
        plot_frame = ttk.Frame(main_frame)
        plot_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create matplotlib figure and canvas
        self.fig, self.ax = plt.subplots(figsize=(12, 3))
        self.ax.set_title("ECG Signal")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Amplitude")
        self.ax.grid(True)
        
        # Initialize empty plot with y-axis from -1 to 1024
        self.ecg_line, = self.ax.plot([], [], 'b-')
        self.ax.set_xlim(0, self.max_ecg_points)
        self.ax.set_ylim(-1, 1024)  # Updated y-axis range
        
        # Create canvas and add to plot frame
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def start_serial_thread(self):
        """Start the serial communication thread"""
        try:
            self.ser = serial.Serial(self.serial_port, self.baudrate, timeout=1)
            self.running = True
            self.thread = threading.Thread(target=self.read_serial_data, daemon=True)
            self.thread.start()
            self.status_var.set(f"Status: Connected to {self.serial_port}")
            self.root.after(100, self.update_interface)
        except Exception as e:
            self.status_var.set(f"Status: Connection failed - {str(e)}")

    def read_serial_data(self):
        """Thread function to read serial data"""
        while self.running and self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8').strip()
                    if line:  # Only process non-empty lines
                        self.data_queue.put(line)
            except Exception as e:
                print(f"Serial read error: {e}")

    def parse_sensor_data(self, raw_line):
        """
        Parse the incoming sensor data.
        Now expects data in format: ambient_temp,body_temp,pressure,depth,water_temp,ecg,bpm,signal,deco_msg
        """
        try:
            # Split the incoming data by commas
            parts = [part.strip() for part in raw_line.split(',')]
            
            # Ensure we have all expected fields (9 fields now with signal)
            if len(parts) >= 9:
                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                
                # Process ECG value (convert to float if possible)
                ecg_value = 0.0
                try:
                    ecg_value = float(parts[5])
                    self.ecg_data.append(ecg_value)
                    if len(self.ecg_data) > self.max_ecg_points:
                        self.ecg_data.pop(0)
                except ValueError:
                    pass
                
                return [
                    timestamp,       # Timestamp
                    parts[0],       # Ambient Temp
                    parts[1],       # Body Temp
                    parts[2],       # Pressure
                    parts[3],       # Depth
                    parts[4],       # Water Temp
                    parts[5],       # ECG Values
                    parts[6],       # BPM
                    parts[7],       # Signal (new field)
                    parts[8]        # Deco Message
                ]
            elif len(parts) == 8:  # For backward compatibility if signal is missing
                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                
                # Process ECG value (convert to float if possible)
                ecg_value = 0.0
                try:
                    ecg_value = float(parts[5])
                    self.ecg_data.append(ecg_value)
                    if len(self.ecg_data) > self.max_ecg_points:
                        self.ecg_data.pop(0)
                except ValueError:
                    pass
                
                return [
                    timestamp,       # Timestamp
                    parts[0],       # Ambient Temp
                    parts[1],       # Body Temp
                    parts[2],       # Pressure
                    parts[3],       # Depth
                    parts[4],       # Water Temp
                    parts[5],       # ECG Values
                    parts[6],       # BPM
                    "N/A",          # Signal (placeholder)
                    parts[7]        # Deco Message
                ]
            else:
                print(f"Unexpected data format: {raw_line}")
                return None
        except Exception as e:
            print(f"Error parsing data: {e}")
            return None

    def update_ecg_plot(self):
        """Update the ECG plot with new data"""
        if len(self.ecg_data) > 0:
            x_data = np.arange(len(self.ecg_data))
            self.ecg_line.set_data(x_data, self.ecg_data)
            # Keep y-axis fixed between -1 and 1024
            self.ax.set_ylim(-1, 1024)
            self.canvas.draw()

    def update_interface(self):
        """Update the GUI with new data"""
        try:
            while not self.data_queue.empty():
                raw_line = self.data_queue.get_nowait()
                parsed_data = self.parse_sensor_data(raw_line)
                
                if parsed_data:
                    self.tree.insert('', 'end', values=parsed_data)
                    # Auto-scroll to the bottom
                    self.tree.yview_moveto(1)
                    
                    # Limit to 1000 rows to prevent memory issues
                    if len(self.tree.get_children()) > 1000:
                        self.tree.delete(self.tree.get_children()[0])
            
            # Update ECG plot
            self.update_ecg_plot()
        
        except queue.Empty:
            pass
        
        self.root.after(100, self.update_interface)

    def start_monitoring(self):
        """Start data monitoring"""
        if not self.running:
            self.running = True
            if not hasattr(self, 'thread') or not self.thread.is_alive():
                self.start_serial_thread()
            self.status_var.set(f"Status: Monitoring {self.serial_port}")

    def stop_monitoring(self):
        """Stop data monitoring"""
        self.running = False
        self.status_var.set("Status: Monitoring stopped")

    def clear_data(self):
        """Clear all displayed data"""
        # Clear table data
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Clear ECG data and plot
        self.ecg_data = []
        self.ecg_line.set_data([], [])
        self.ax.set_ylim(-1, 1024)  # Reset y-axis limits
        self.canvas.draw()

    def on_closing(self):
        """Cleanup before closing"""
        self.running = False
        if hasattr(self, 'ser') and self.ser and self.ser.is_open:
            self.ser.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SensorMonitorApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()