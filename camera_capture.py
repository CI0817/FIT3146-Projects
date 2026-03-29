#!/usr/bin/env python3
# Last Modified: 29.03.26 2.52PM

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

    # Global adjustments
    img = ImageEnhance.Color(img).enhance(0.82)
    img = ImageEnhance.Contrast(img).enhance(0.90)
    img = ImageEnhance.Brightness(img).enhance(1.02)

    pixels = img.load()
    width, height = img.size

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]

            # Approximate luminance
            lum = 0.299 * r + 0.587 * g + 0.114 * b

            # Warm overall tone
            r *= 1.08
            g *= 1.02
            b *= 0.90

            # Lift blacks / fade shadows
            if lum < 90:
                r = r * 0.92 + 14
                g = g * 0.92 + 12
                b = b * 0.92 + 10

            # Soften highlights slightly
            elif lum > 190:
                r = r * 0.97 + 3
                g = g * 0.97 + 3
                b = b * 0.97 + 3

            r = max(0, min(255, int(r)))
            g = max(0, min(255, int(g)))
            b = max(0, min(255, int(b)))

            pixels[x, y] = (r, g, b)

    # Slight softness to reduce digital sharpness
    img = img.filter(ImageFilter.GaussianBlur(radius=0.35))

    img.save(output_filename, quality=95)
    print(f"Vintage photo saved: {output_filename}")

def apply_classic_chrome_filter(input_filename, output_filename):
    img = Image.open(input_filename).convert("RGB")

    # Global adjustments for a "hard, deep" base look
    # 1. More dramatic base desaturation
    img = ImageEnhance.Color(img).enhance(0.70) 
    # 2. Key: INCREASE contrast for a hard, punchy look
    img = ImageEnhance.Contrast(img).enhance(1.18)
    # 3. Slight darkening for depth
    img = ImageEnhance.Brightness(img).enhance(0.97)

    pixels = img.load()
    width, height = img.size

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]

            lum = 0.299 * r + 0.587 * g + 0.114 * b

            # Selective Color Muting (Midtones and up)
            if lum > 80:
                # Key Classic Chrome Color Shifts:
                # 1. Deep red suppression
                r *= 0.90 
                # 2. Deep green suppression
                g *= 0.93 
                # 3. Add deep, distinctive blues (small lift)
                b *= 1.05

                # Highlight compression (your existing logic is good)
                if lum > 190:
                    r = r * 0.97 + 2
                    g = g * 0.97 + 2
                    b = b * 0.97 + 2
            
            # Deeper Shadow Management (Lum < 80)
            else: 
                # We want true, deep blacks.
                # Deep color suppression in shadows to match.
                r *= 0.88
                g *= 0.92
                b *= 0.98

            # Clamping (must remain)
            r = max(0, min(255, int(r)))
            g = max(0, min(255, int(g)))
            b = max(0, min(255, int(b)))

            pixels[x, y] = (r, g, b)

    # Blur - Classic Chrome is often sharp. Skipping this or 
    # using an extremely low radius.
    # img = img.filter(ImageFilter.GaussianBlur(radius=0.18))

    img.save(output_filename, quality=95)
    print(f"Realistic Classic Chrome photo saved: {output_filename}")

def apply_classic_negative_filter(input_filename, output_filename):
    img = Image.open(input_filename).convert("RGB")

    # 1. Back off the contrast just a touch to stop the banding
    img = ImageEnhance.Color(img).enhance(0.90) 
    img = ImageEnhance.Contrast(img).enhance(1.12) # Dropped from 1.20
    img = ImageEnhance.Brightness(img).enhance(0.98)

    pixels = img.load()
    width, height = img.size

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            lum = 0.299 * r + 0.587 * g + 0.114 * b

            if lum < 80:
                # 2. Softer cyan shift, plus a tiny lift (+3/+5) to stop pixelation
                r = r * 0.90 + 3
                g = g * 0.96 + 3
                b = b * 1.02 + 5
            elif lum > 170:
                # Highlights: Gentle warm push
                r *= 1.03
                g *= 1.01
                b *= 0.97
            else:
                # Midtones: Very close to neutral to protect walls
                r *= 1.01 
                g *= 0.98
                b *= 0.99

            r = max(0, min(255, int(r)))
            g = max(0, min(255, int(g)))
            b = max(0, min(255, int(b)))

            pixels[x, y] = (r, g, b)

    # 3. Add a very slight blur to smooth out the colour transitions
    img = img.filter(ImageFilter.GaussianBlur(radius=0.25))

    img.save(output_filename, quality=95)
    print(f"Smoothed Classic Negative photo saved: {output_filename}")

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
    classicNeg_filename = os.path.join(SAVE_DIR, f"photo_{timestamp}_classicNeg.jpg")

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
        apply_classic_negative_filter(filename, classicNeg_filename)
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