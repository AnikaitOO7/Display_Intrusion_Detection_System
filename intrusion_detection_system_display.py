import tkinter as tk
import tkinter.messagebox
import serial
import threading
from collections import defaultdict
import os
import logging
from datetime import datetime

# Setup serial port for LoRa module
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 115200
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

# Setup logging
LOG_FILE = 'intrusion_log.txt'

# Create a logger and set the logging level
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create a file handler for writing logs to the file
file_handler = logging.FileHandler(LOG_FILE)

# Create a stream handler for writing logs to the console
stream_handler = logging.StreamHandler()

# Create a formatter and add it to both handlers
formatter = logging.Formatter('%(asctime)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Add both handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# GUI setup
root = tk.Tk()
root.title("Intrusion Detection System")
root.geometry("1000x800")
root.configure(bg='black')

# Initialize sensor status frames and labels
status_frames = {}
status_labels = {}
sensor_counters = defaultdict(lambda: defaultdict(int))  # Counters for consecutive detections
heartbeat_status = defaultdict(bool)
reset_timer = None

for node in range(1, 13):  # Assuming 13 nodes
    for sensor in range(1, 5):  # 4 sensors per node
        frame = tk.Frame(root, bg='black', bd=2, relief='sunken')
        frame.grid(row=node, column=sensor, padx=12, pady=12)

        label_text = f"Node {node} Sensor {sensor}: OK"
        label = tk.Label(frame, text=label_text, fg="green", bg='black')
        label.pack()

        status_frames[(node, sensor)] = frame
        status_labels[(node, sensor)] = label

# Function to update sensor status in the GUI
def update_sensor_status(node, sensor, status):
    key = (node, sensor)
    sensor_counters[key][status] += 1

    if sensor_counters[key][status] >= 3:  # Confirm intrusion after 3 consecutive messages
        update_label(node, sensor, "Intrusion", "red")
        tkinter.messagebox.showwarning("Intrusion Detected", f"Intrusion detected at Node {node}, Sensor {sensor}")
        sensor_counters[key] = defaultdict(int)  # Reset counters after confirming intrusion
        log_intrusion(node, sensor)

        reset_sensors_after_delay()

    elif not status:
        heartbeat_status[node] = True  # Node is giving heartbeat
        update_all_sensors(node, "OK", "green")

# Update label text and color
def update_label(node, sensor, text, color):
    label = status_labels[(node, sensor)]
    label.config(text=f"Node {node} Sensor {sensor}: {text}", fg=color)
    label.pack()

# Update all sensors for a node
def update_all_sensors(node, text, color):
    for s in range(1, 5):
        update_label(node, s, text, color)

# Reset all sensors after 10 seconds
def reset_sensors_after_delay():
    global reset_timer
    if reset_timer is not None:
        root.after_cancel(reset_timer)
    reset_timer = root.after(10000, reset_all_sensors)

# Log intrusion event with node number, sensor number, date, and time
def log_intrusion(node, sensor):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_message = f"Intrusion detected at Node {node}, Sensor {sensor} - {timestamp}"
    logger.info(log_message)

# Function to read data from LoRa module
def read_lora_data():
    while True:
        if ser.in_waiting > 0:
            message = ser.readline().decode().strip()
            if message.isnumeric():
                try:
                    node_id = int(message[:1])
                    sensor_id = int(message[1:])
                    is_intrusion = sensor_id != 0
                    if is_intrusion:
                        update_sensor_status(node_id, sensor_id, True)
                    else:
                        update_all_sensors(node_id, "OK", "green")
                except ValueError:
                    print("Error processing message:", message)
            else:
                print("Non-standard message received:", message)

# Check for missing heartbeat
def check_heartbeat():
    for node in range(1, 13):
        if not heartbeat_status[node]:
            update_all_sensors(node, "Out", "yellow")
        heartbeat_status[node] = False  # Reset heartbeat status
    root.after(5000, check_heartbeat)  # Check every 5 seconds

# Reset all sensors to OK
def reset_all_sensors():
    for node in range(1, 13):
        for s in range(1, 5):
            update_label(node, s, "OK", "green")

# Start a thread for reading LoRa data and checking heartbeat
threading.Thread(target=read_lora_data, daemon=True).start()
root.after(5000, check_heartbeat)

# Start the GUI loop
root.mainloop()