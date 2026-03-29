#!/usr/bin/env python3
# Last Modified: 29.03.26 1.51PM

from gpiozero import Button # handles the GPIO input (the physical button)
from signal import pause # keeps the script running forever
from datetime import datetime # used to timestamp filenames
import subprocess # lets Python run shell commands (fswebcam)
import os # for file paths and folder creation
from PIL import Image, ImageEnhance, ImageFilter # Python Imagery Library (PIL)

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

def apply_vintage_filter(input_filename, output_filename):
    img = Image.open(input_filename).convert("RGB")

    # Slightly reduce saturation
    img = ImageEnhance.Color(img).enhance(0.85)

    # Slightly lower contrast
    img = ImageEnhance.Contrast(img).enhance(0.92)

    # Slightly increase brightness
    img = ImageEnhance.Brightness(img).enhance(1.03)

    # Add a warm tone
    pixels = img.load()
    width, height = img.size

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]

            r = min(255, int(r * 1.08))
            g = min(255, int(g * 1.02))
            b = min(255, int(b * 0.92))

            pixels[x, y] = (r, g, b)

    # Slight blur
    img = img.filter(ImageFilter.GaussianBlur(radius=0.3))

    img.save(output_filename, quality=95)
    print(f"Filtered photo saved: {output_filename}")

def apply_classic_chrome_filter(input_filename, output_filename):
    img = Image.open(input_filename).convert("RGB")

    # 1) Lower saturation for muted documentary-style color
    img = ImageEnhance.Color(img).enhance(0.78)

    # 2) Slight contrast shaping
    img = ImageEnhance.Contrast(img).enhance(0.95)

    # 3) Slightly reduce brightness so it does not feel too digital/clean
    img = ImageEnhance.Brightness(img).enhance(0.97)

    # 4) Classic Chrome-style channel tuning:
    #    - suppress reds / magenta a bit
    #    - cool shadows overall by slightly favoring blue
    #    - keep greens natural but not vivid
    pixels = img.load()
    width, height = img.size

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]

            r = int(r * 0.93)   # reduce red
            g = int(g * 0.97)   # slightly mute green
            b = int(b * 1.04)   # slight cool shift

            # clamp to valid range
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))

            pixels[x, y] = (r, g, b)

    # 5) Slight blur to reduce digital sharpness
    img = img.filter(ImageFilter.GaussianBlur(radius=0.25))

    img.save(output_filename, quality=95)
    print(f"Classic Chrome-style photo saved: {output_filename}")

# Global variable to avoid multiple presses
busy = False

def take_photo():
    # Look at the global variable, busy
    global busy
    if busy:
        print("Still taking previous photo...")
        return
    
    busy = True
    print("Taking photo...")
    
    # Get current datetime
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # Create a filename based on datetime, all files are unique
    filename = os.path.join(SAVE_DIR, f"photo_{timestamp}.jpg")
    # Create a filename for the filtered image
    filtered_filename = os.path.join(SAVE_DIR, f"photo_{timestamp}_vintage.jpg")
    classicChrome_filename = os.path.join(SAVE_DIR, f"photo_{timestamp}_classicChrome.jpg")

    # fswebcam command to be used
    cmd = [
        "fswebcam",
        "-r", "1280x720", # resolution
        "--flip", "h", # mirror image
        "-S", "20", # discard the first 20 frames (could be blurry)
        "--no-banner", # remove default banner
        filename
    ]

    try:
        # Run the command
        # check=True: raises error if it fails
        subprocess.run(cmd, check=True)
        print(f"Photo saved: {filename}")
        # Run the vintage filter function
        apply_vintage_filter(filename, filtered_filename)
        apply_classic_chrome_filter(filename, classicChrome_filename)
    # If sth fails
    except subprocess.CalledProcessError as e:
        print(f"Failed to take photo: {e}")
    # If everything went ok, reset the busy flag
    finally:
        busy = False

# When GPIO17 detects a press, call the take_photo function
button.when_pressed = take_photo

# Wait for the button press
# Once pressed and the function completed, the script contiue waiting
print("Waiting for button press...")
pause()