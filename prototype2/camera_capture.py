#!/usr/bin/env python3
# Last Modified: 29.03.26 3.53PM

from gpiozero import Button # handles the GPIO input (the physical button)
from signal import pause # keeps the script running forever
from datetime import datetime # used to timestamp filenames
import subprocess # lets Python run shell commands (fswebcam)
import os # for file paths and folder creation
from PIL import Image, ImageEnhance, ImageFilter # Python Imagery Library (PIL)
from RPLCD.i2c import CharLCD
import time

shutter_button = Button(17, pull_up=True, bounce_time=0.1)
filter_button = Button(27, pull_up=True, bounce_time=0.1)
mirror_button = Button(22, pull_up=True, bounce_time=0.1)
shutdown_button = Button(26, pull_up=True, bounce_time=0.1, hold_time=3)

# LCD initialisation
# 'PCF8574' is the most common I2C backpack chip. 
# 0x27 is the default address for most modules.
lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=16, rows=2, dotsize=8)
lcd.clear()

# Create or get the path to save picture
# exist_ok=True: wont crash if folder already exists
SAVE_DIR = "Photos"
os.makedirs(SAVE_DIR, exist_ok=True)

# Available filters: 0=None, 1=Vintage, 2=Chrome, 3=Negative, 4=Acros
filters = ["None", "Vintage", "Classic Chrome", "Classic Negative", "Acros B&W"]
current_filter_index = 0
mirror_enabled = True # Default to mirrored
busy = False

def safe_shutdown():
    lcd.clear()
    lcd.write_string("Shutting down...")
    time.sleep(1)
    lcd.backlight_enabled = False
    lcd.close()
    os.system("sudo shutdown -h now")

def update_lcd():
    """Updates the 16x2 display with current settings."""
    lcd.clear()
    # Line 1: Filter Name
    lcd.write_string(f"F: {filters[current_filter_index]}")
    # Line 2: Mirror Status
    lcd.cursor_pos = (1, 0)
    mirror_text = "Mirror: ON" if mirror_enabled else "Mirror: OFF"
    lcd.write_string(mirror_text)

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

def apply_acros_bw_filter(input_filename, output_filename):
    img = Image.open(input_filename).convert("RGB")

    # Acros has a strong, punchy contrast right from the start
    img = ImageEnhance.Contrast(img).enhance(1.25)
    
    pixels = img.load()
    width, height = img.size

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]

            # Custom B&W conversion: weighting green a bit more gives smoother tones
            lum = 0.25 * r + 0.65 * g + 0.10 * b

            # Create that rich film depth with an S-curve
            if lum < 75:
                # Darken the shadows to make them deep and rich
                lum *= 0.88
            elif lum > 180:
                # Keep the highlights crisp and bright
                lum *= 1.05

            lum = max(0, min(255, int(lum)))

            # Set all channels to the same value for pure grayscale
            pixels[x, y] = (lum, lum, lum)

    img.save(output_filename, quality=95)
    print(f"Acros B&W photo saved: {output_filename}")

def cycle_filter():
    global current_filter_index
    current_filter_index = (current_filter_index + 1) % len(filters)
    print(f"Selected Filter: {filters[current_filter_index]}")
    update_lcd()

def toggle_mirror():
    global mirror_enabled
    mirror_enabled = not mirror_enabled
    print(f"Mirroring: {'ON' if mirror_enabled else 'OFF'}")
    update_lcd()

def take_photo():
    global busy
    if busy:
        return
    
    busy = True
    lcd.clear()
    lcd.write_string("Capturing...")
    print(f"Capturing with {filters[current_filter_index]} (Mirror: {mirror_enabled})...")
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    raw_filename = os.path.join(SAVE_DIR, f"raw_{timestamp}.jpg")
    final_filename = os.path.join(SAVE_DIR, f"photo_{timestamp}.jpg")

    # Build the fswebcam command
    cmd = [
        "fswebcam",
        "-r", "1280x720",
        "-S", "20",
        "--no-banner",
        raw_filename
    ]
    
    # Add horizontal flip ONLY if mirror_enabled is True
    if mirror_enabled:
        cmd.insert(5, "--flip")
        cmd.insert(6, "h")

    try:
        subprocess.run(cmd, check=True)
        
        # Apply the chosen filter
        idx = current_filter_index
        if idx == 0: # None
            os.rename(raw_filename, final_filename)
            print(f"Photo saved (No filter): {final_filename}")
        elif idx == 1:
            apply_vintage_filter(raw_filename, final_filename)
        elif idx == 2:
            apply_classic_chrome_filter(raw_filename, final_filename)
        elif idx == 3:
            apply_classic_negative_filter(raw_filename, final_filename)
        elif idx == 4:
            apply_acros_bw_filter(raw_filename, final_filename)
            
        # Clean up the raw file if a filter was applied
        if idx != 0 and os.path.exists(raw_filename):
            os.remove(raw_filename)
        
        lcd.clear()
        lcd.write_string("Photo Saved!")

    except subprocess.CalledProcessError as e:
        lcd.clear()
        lcd.write_string("Error!")
        print(f"Failed: {e}")
    finally:
        busy = False
        # Return to settings display after a short delay
        import time
        time.sleep(2)
        update_lcd()

shutter_button.when_pressed = take_photo
filter_button.when_pressed = cycle_filter
mirror_button.when_pressed = toggle_mirror

# This only runs if you hold the button for 3 seconds
shutdown_button.when_held = safe_shutdown

print("Camera Ready!")
print(f"Default: {filters[current_filter_index]} | Mirror: {mirror_enabled}")
update_lcd()
pause()