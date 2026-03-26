#!/usr/bin/env python3
# Last Modified: 26.03.26 11.20AM

from gpiozero import Button # handles the GPIO input (the physical button)
from signal import pause # keeps the script running forever
from datetime import datetime # used to timestamp filenames
import subprocess # lets Python run shell commands (fswebcam)
import os # for file paths and folder creation

# Connect physical button to pin 11
# 17: GPIO17 (physical pin 11)
# pull_up=True: uses internal pull-up resistor
# default state: HIGH
# pressed = LOW (connected to GND)
# bounce_time=0.1: filters noisy button presses (debouncing)
button = Button(17, pull_up=True, bounce_time=0.1)

# Create or get the path to save picture
# exist_ok=True: won’t crash if folder already exists
SAVE_DIR = "Photos"
os.makedirs(SAVE_DIR, exist_ok=True)

# Global variable to avoid multiple presses
busy = False

def take_photo():
    # Look at the global variable, busy
    global busy
    if busy:
        print("Still taking previous photo...")
        return
    
    # Get current datetime
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # Create a filename based on datetime, all files are unique
    filename = os.path.join(SAVE_DIR, f"photo_{timestamp}.jpg")

    # fswebcam command to be used
    cmd = [
        "fswebcam",
        "-r", "1280x720", # resolution
        "-S", "20", # discard the first 20 frames (could be blurry)
        "--no-banner", # remove default banner
        filename
    ]

    try:
        # Run the command
        # check=True: raises error if it fails
        subprocess.run(cmd, check=True)
        print(f"Photo saved: {filename}")
    # If sth fails
    except subprocess.CalledProcessError as e:
        print(f"Failed to take photo: {e}")
    # if everything went ok, reset the busy flag
    finally:
        busy = False

# When GPIO17 detects a press, call the take_photo function
button.when_pressed = take_photo

# Wait for the button press
# Once pressed and the function completed, the script contiue waiting
print("Waiting for button press...")
pause()