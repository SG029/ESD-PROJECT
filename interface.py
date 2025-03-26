import tkinter as tk
from tkinter import ttk
import random
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk
import time

class DivingMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Diving Metrics Monitor")
        self.root.geometry("1000x700")
        self.root.configure(bg='#003366')
        
        self.spo2 = 98
        self.current_depth = 0
        self.ascent_rate = 0
        self.heart_rate = 72
        self.decompression_stop_active = False
        self.decompression_stop_depth = 0
        self.decompression_stop_time = 0
        
        self.create_header()
        self.create_metrics_display()
        self.create_depth_chart()
        self.create_decompression_panel()
        self.create_alert_panel()
        
        self.simulate_dive()
    
    def create_header(self):
        header_frame = tk.Frame(self.root, bg='#001a33')
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title_label = tk.Label(
            header_frame, 
            text="DIVING METRICS MONITOR", 
            font=('Helvetica', 18, 'bold'), 
            fg='white', 
            bg='#001a33'
        )
        title_label.pack(pady=10)
        
        self.time_label = tk.Label(
            header_frame, 
            text="", 
            font=('Helvetica', 12), 
            fg='white', 
            bg='#001a33'
        )
        self.time_label.pack(side=tk.RIGHT, padx=20)
        self.update_time()
    
    def create_metrics_display(self):
        metrics_frame = tk.Frame(self.root, bg='#003366')
        metrics_frame.pack(fill=tk.X, padx=10, pady=10)
        
        spo2_frame = tk.Frame(metrics_frame, bg='#004080', bd=2, relief=tk.RIDGE)
        spo2_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        tk.Label(
            spo2_frame, 
            text="SpO₂", 
            font=('Helvetica', 14), 
            fg='white', 
            bg='#004080'
        ).pack(pady=(5,0))
        
        self.spo2_label = tk.Label(
            spo2_frame, 
            text=f"{self.spo2}%", 
            font=('Helvetica', 24, 'bold'), 
            fg=self.get_spo2_color(), 
            bg='#004080'
        )
        self.spo2_label.pack(pady=(0,5))
        
        hr_frame = tk.Frame(metrics_frame, bg='#004080', bd=2, relief=tk.RIDGE)
        hr_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        tk.Label(
            hr_frame, 
            text="HEART RATE", 
            font=('Helvetica', 14), 
            fg='white', 
            bg='#004080'
        ).pack(pady=(5,0))
        
        self.hr_label = tk.Label(
            hr_frame, 
            text=f"{self.heart_rate} BPM", 
            font=('Helvetica', 24, 'bold'), 
            fg=self.get_hr_color(), 
            bg='#004080'
        )
        self.hr_label.pack(pady=(0,5))
        
        ascent_frame = tk.Frame(metrics_frame, bg='#004080', bd=2, relief=tk.RIDGE)
        ascent_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        
        tk.Label(
            ascent_frame, 
            text="ASCENT RATE", 
            font=('Helvetica', 14), 
            fg='white', 
            bg='#004080'
        ).pack(pady=(5,0))
        
        self.ascent_label = tk.Label(
            ascent_frame, 
            text=f"{self.ascent_rate} m/min", 
            font=('Helvetica', 24, 'bold'), 
            fg=self.get_ascent_color(), 
            bg='#004080'
        )
        self.ascent_label.pack(pady=(0,5))
        
        depth_frame = tk.Frame(metrics_frame, bg='#004080', bd=2, relief=tk.RIDGE)
        depth_frame.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")
        
        tk.Label(
            depth_frame, 
            text="CURRENT DEPTH", 
            font=('Helvetica', 14), 
            fg='white', 
            bg='#004080'
        ).pack(pady=(5,0))
        
        self.depth_label = tk.Label(
            depth_frame, 
            text=f"{self.current_depth} m", 
            font=('Helvetica', 24, 'bold'), 
            fg='white', 
            bg='#004080'
        )
        self.depth_label.pack(pady=(0,5))
        
        for i in range(4):
            metrics_frame.columnconfigure(i, weight=1)
    
    def create_depth_chart(self):
        chart_frame = tk.Frame(self.root, bg='#003366')
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.fig, self.ax = plt.subplots(figsize=(8, 4), facecolor='#003366')
        self.ax.set_facecolor('#003366')
        self.ax.invert_yaxis()
        self.ax.set_title('Depth Profile', color='white')
        self.ax.set_xlabel('Time', color='white')
        self.ax.set_ylabel('Depth (m)', color='white')
        self.ax.tick_params(colors='white')
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white') 
        self.ax.spines['right'].set_color('white')
        self.ax.spines['left'].set_color('white')
        
        self.depth_line, = self.ax.plot([], [], 'c-', linewidth=2)
        self.current_pos = self.ax.plot([], [], 'ro')[0]
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.depth_data = []
        self.time_data = []
        self.start_time = time.time()
    
    def create_decompression_panel(self):
        deco_frame = tk.Frame(self.root, bg='#004080', bd=2, relief=tk.RIDGE)
        deco_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(
            deco_frame, 
            text="DECOMPRESSION INFORMATION", 
            font=('Helvetica', 14, 'bold'), 
            fg='white', 
            bg='#004080'
        ).pack(pady=(5,0))
        
        self.deco_info_label = tk.Label(
            deco_frame, 
            text="No decompression stop required", 
            font=('Helvetica', 12), 
            fg='white', 
            bg='#004080'
        )
        self.deco_info_label.pack(pady=5)
        
        deco_details_frame = tk.Frame(deco_frame, bg='#004080')
        deco_details_frame.pack(pady=5)
        
        tk.Label(
            deco_details_frame, 
            text="Next Stop:", 
            font=('Helvetica', 12), 
            fg='white', 
            bg='#004080'
        ).grid(row=0, column=0, padx=5, sticky='e')
        
        self.next_stop_label = tk.Label(
            deco_details_frame, 
            text="None", 
            font=('Helvetica', 12, 'bold'), 
            fg='white', 
            bg='#004080'
        )
        self.next_stop_label.grid(row=0, column=1, padx=5, sticky='w')
        
        tk.Label(
            deco_details_frame, 
            text="Stop Depth:", 
            font=('Helvetica', 12), 
            fg='white', 
            bg='#004080'
        ).grid(row=1, column=0, padx=5, sticky='e')
        
        self.stop_depth_label = tk.Label(
            deco_details_frame, 
            text="0 m", 
            font=('Helvetica', 12, 'bold'), 
            fg='white', 
            bg='#004080'
        )
        self.stop_depth_label.grid(row=1, column=1, padx=5, sticky='w')
        
        tk.Label(
            deco_details_frame, 
            text="Stop Time:", 
            font=('Helvetica', 12), 
            fg='white', 
            bg='#004080'
        ).grid(row=2, column=0, padx=5, sticky='e')
        
        self.stop_time_label = tk.Label(
            deco_details_frame, 
            text="0 min", 
            font=('Helvetica', 12, 'bold'), 
            fg='white', 
            bg='#004080'
        )
        self.stop_time_label.grid(row=2, column=1, padx=5, sticky='w')
    
    def create_alert_panel(self):
        self.alert_frame = tk.Frame(self.root, bg='#660000', bd=2, relief=tk.RIDGE)
        self.alert_label = tk.Label(
            self.alert_frame, 
            text="", 
            font=('Helvetica', 12, 'bold'), 
            fg='white', 
            bg='#660000'
        )
        self.alert_label.pack(pady=5)
        self.alert_frame.pack_forget()
    
    def update_time(self):
        current_time = time.strftime("%H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)
    
    def get_spo2_color(self):
        if self.spo2 >= 95:
            return '#00ff00'
        elif 90 <= self.spo2 < 95:
            return '#ffff00'
        else:
            return '#ff0000'
    
    def get_hr_color(self):
        if 60 <= self.heart_rate <= 100:
            return '#00ff00'
        elif 40 <= self.heart_rate < 60 or 100 < self.heart_rate <= 120:
            return '#ffff00'
        else:
            return '#ff0000'
    
    def get_ascent_color(self):
        if self.ascent_rate <= 9:
            return '#00ff00'
        elif 9 < self.ascent_rate <= 18:
            return '#ffff00'
        else:
            return '#ff0000'
    
    def update_metrics(self):
        self.spo2_label.config(text=f"{self.spo2}%", fg=self.get_spo2_color())
        self.hr_label.config(text=f"{self.heart_rate} BPM", fg=self.get_hr_color())
        self.ascent_label.config(text=f"{self.ascent_rate} m/min", fg=self.get_ascent_color())
        self.depth_label.config(text=f"{self.current_depth} m")
        
        self.update_decompression_info()
        self.update_depth_chart()
        self.check_alerts()
    
    def update_decompression_info(self):
        if self.current_depth > 30 and not self.decompression_stop_active:
            self.decompression_stop_active = True
            self.decompression_stop_depth = 5
            self.decompression_stop_time = 3
            
            self.deco_info_label.config(text="DECOMPRESSION STOP REQUIRED!")
            self.next_stop_label.config(text=f"{self.decompression_stop_depth} m")
            self.stop_depth_label.config(text=f"{self.decompression_stop_depth} m")
            self.stop_time_label.config(text=f"{self.decompression_stop_time} min")
        elif self.current_depth <= 5 and self.decompression_stop_active:
            if self.decompression_stop_time > 0:
                self.decompression_stop_time -= 0.1
                self.stop_time_label.config(text=f"{max(0, self.decompression_stop_time):.1f} min")
            else:
                self.decompression_stop_active = False
                self.deco_info_label.config(text="No decompression stop required")
                self.next_stop_label.config(text="None")
                self.stop_depth_label.config(text="0 m")
                self.stop_time_label.config(text="0 min")
    
    def update_depth_chart(self):
        current_time = time.time() - self.start_time
        self.time_data.append(current_time)
        self.depth_data.append(self.current_depth)
        
        if len(self.time_data) > 100:
            self.time_data = self.time_data[-100:]
            self.depth_data = self.depth_data[-100:]
        
        self.depth_line.set_data(self.time_data, self.depth_data)
        self.current_pos.set_data([current_time], [self.current_depth])
        
        self.ax.relim()
        self.ax.autoscale_view()
        self.ax.set_xlim(left=max(0, current_time-50), right=current_time+5)
        
        self.canvas.draw()
    
    def check_alerts(self):
        alerts = []
        
        if self.spo2 < 90:
            alerts.append(f"LOW SpO₂: {self.spo2}%")
        
        if self.ascent_rate > 18:
            alerts.append(f"DANGEROUS ASCENT RATE: {self.ascent_rate} m/min")
        
        if self.heart_rate < 40 or self.heart_rate > 120:
            alerts.append(f"ABNORMAL HEART RATE: {self.heart_rate} BPM")
        
        if self.decompression_stop_active and self.current_depth > self.decompression_stop_depth + 2:
            alerts.append(f"MISSED DECO STOP AT {self.decompression_stop_depth}m")
        
        if alerts:
            self.alert_label.config(text="\n".join(alerts))
            self.alert_frame.pack(fill=tk.X, padx=10, pady=5)
        else:
            self.alert_frame.pack_forget()
    
    def simulate_dive(self):
        if not hasattr(self, 'dive_phase'):
            self.dive_phase = 'descending'
            self.max_depth = random.randint(15, 40)
            self.bottom_time = random.randint(5, 20)
        
        if self.dive_phase == 'descending':
            self.current_depth = min(self.current_depth + random.uniform(0.5, 2), self.max_depth)
            self.ascent_rate = 0
            self.heart_rate = min(120, 70 + int(self.current_depth * 1.5))
            self.spo2 = max(90, 98 - int(self.current_depth / 10))
            
            if self.current_depth >= self.max_depth:
                self.dive_phase = 'bottom'
                self.bottom_start_time = time.time()
        
        elif self.dive_phase == 'bottom':
            self.current_depth = self.max_depth + random.uniform(-1, 1)
            self.ascent_rate = 0
            self.heart_rate = 80 + int(self.max_depth / 2)
            self.spo2 = max(85, 95 - int(self.max_depth / 8))
            
            if time.time() - self.bottom_start_time > self.bottom_time:
                self.dive_phase = 'ascending'
        
        elif self.dive_phase == 'ascending':
            ascent_speed = random.uniform(5, 15)
            self.current_depth = max(0, self.current_depth - ascent_speed * 0.1)
            self.ascent_rate = ascent_speed
            self.heart_rate = 70 + int(ascent_speed * 2)
            self.spo2 = min(100, 90 + int((self.max_depth - self.current_depth) / 3))
            
            if self.current_depth <= 0:
                self.dive_phase = 'surface'
                self.current_depth = 0
                self.ascent_rate = 0
        
        elif self.dive_phase == 'surface':
            self.heart_rate = 65 + random.randint(-5, 5)
            self.spo2 = 98 + random.randint(-2, 2)
        
        self.spo2 += random.randint(-1, 1)
        self.heart_rate += random.randint(-2, 2)
        
        self.update_metrics()
        
        if self.dive_phase != 'surface':
            self.root.after(500, self.simulate_dive)
        else:
            self.root.after(5000, self.reset_simulation)
    
    def reset_simulation(self):
        self.dive_phase = 'descending'
        self.current_depth = 0
        self.max_depth = random.randint(15, 40)
        self.bottom_time = random.randint(5, 20)
        self.simulate_dive()

if __name__ == "__main__":
    root = tk.Tk()
    app = DivingMonitorApp(root)
    root.mainloop()