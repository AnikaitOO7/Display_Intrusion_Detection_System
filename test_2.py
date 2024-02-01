import tkinter as tk
import tkinter.messagebox
# import serial  # Commenting out the problematic line
import threading
from collections import defaultdict
import os
import logging
from datetime import datetime

# Setup logging
LOG_FILE = 'intrusion_log.txt'  # Update this with the correct file path
logger = logging.getLogger()
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(LOG_FILE)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# GUI setup
root = tk.Tk()
root.title("Intrusion Detection System")
root.geometry("1200x800")
root.configure(bg='black')

# Initialize sensor status frames and labels
status_frames = {}
status_labels = {}
sensor_counters = defaultdict(lambda: defaultdict(int))
heartbeat_status = defaultdict(bool)
reset_timer = None

# Log screen variables
log_screen = None
log_text = tk.StringVar()
log_text.set("")  # Initial log text

# Intrusion display variables
intrusion_display = None

# Function to update sensor status in the GUI
def update_sensor_status(node, sensor, status):
    key = (node, sensor)
    sensor_counters[key][status] += 1

    if sensor_counters[key][status] >= 3:
        update_label(node, sensor, "Intrusion", "red")
        tkinter.messagebox.showwarning("Intrusion Detected", f"Intrusion detected at Node {node}, Sensor {sensor}")
        sensor_counters[key] = defaultdict(int)
        log_intrusion(node, sensor)
        reset_sensors_after_delay()

    elif not status:
        heartbeat_status[node] = True
        update_all_sensors(node, "OK", "green")

# Update label text and color
def update_label(node, sensor, text, color):
    label = status_labels[(node, sensor)]
    label.config(text=f"Node {node} Sensor {sensor}: {text}", fg=color)

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

# Check for missing heartbeat
def check_heartbeat():
    for node in range(1, 13):
        if not heartbeat_status[node]:
            update_all_sensors(node, "Out", "yellow")
        heartbeat_status[node] = False
    root.after(5000, check_heartbeat)

# Reset all sensors to OK
def reset_all_sensors():
    for node in range(1, 13):
        for s in range(1, 5):
            update_label(node, s, "OK", "green")

# Function to toggle log screen visibility
def toggle_log_screen():
    if log_screen_button_var.get():
        create_log_screen()
    else:
        destroy_log_screen()

# Function to create log screen
def create_log_screen():
    global log_screen
    log_screen = tk.Frame(root, bg='white', bd=2, relief='sunken')
    log_screen.grid(row=0, column=4, rowspan=14, padx=12, pady=12)

    # Add log content here if needed
    log_label = tk.Label(log_screen, text="Log Screen", font=("Helvetica", 16), bg='white')
    log_label.pack()

    # Reset button for log screen
    reset_button = tk.Button(log_screen, text="Reset Log", command=reset_log, bg='red', fg='white')
    reset_button.pack()

# Function to destroy log screen
def destroy_log_screen():
    if 'log_screen' in globals() and log_screen is not None:
        log_screen.destroy()

# Function to reset log content
def reset_log():
    log_text.set("")  # Clear log text

# Function to toggle intrusion display visibility
def toggle_intrusion_display():
    if intrusion_display_button_var.get():
        create_intrusion_display()
    else:
        destroy_intrusion_display()

# Function to create intrusion display
def create_intrusion_display():
    global intrusion_display
    intrusion_display = tk.Frame(root, bg='white', bd=2, relief='sunken')
    intrusion_display.grid(row=0, column=8, rowspan=14, padx=12, pady=12)

    # Add intrusion display content here if needed
    intrusion_label = tk.Label(intrusion_display, text="Intrusion Display", font=("Helvetica", 16), bg='white')
    intrusion_label.pack()

# Function to destroy intrusion display
def destroy_intrusion_display():
    if 'intrusion_display' in globals() and intrusion_display is not None:
        intrusion_display.destroy()

# Log Screen Button
log_screen_button_var = tk.BooleanVar()
log_screen_button = tk.Checkbutton(root, text="on/off Log Screen", variable=log_screen_button_var, command=toggle_log_screen, bg='black', fg='white')
log_screen_button.grid(row=14, column=4, pady=10)

# Intrusion Display Button
intrusion_display_button_var = tk.BooleanVar()
intrusion_display_button = tk.Checkbutton(root, text="on/off Intrusion Display", variable=intrusion_display_button_var, command=toggle_intrusion_display, bg='black', fg='white')
intrusion_display_button.grid(row=15, column=4, pady=10)

# Update sensor status frames and labels based on connectivity
for node in range(1, 13):
    for sensor in range(1, 5):
        frame = tk.Frame(root, bg='black', bd=2, relief='sunken')
        frame.grid(row=node, column=sensor, padx=12, pady=12)

        label_text = f"Node {node} Sensor {sensor}: Not Connected"
        label = tk.Label(frame, text=label_text, fg="yellow", bg='black')
        label.pack()

        status_frames[(node, sensor)] = frame
        status_labels[(node, sensor)] = label

# Start a thread for checking heartbeat
threading.Thread(target=check_heartbeat, daemon=True).start()

# Start the GUI loop
root.mainloop()
