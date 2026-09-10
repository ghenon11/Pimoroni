import time
import unicornhat as uh
import logging
import sounddevice as sd
import numpy as np
import argparse
import signal
import sys
from unicornhat import clear, show
import os
import glob
import shutil



# ============================================================
# DJ COLOR SCALE
# ============================================================
COLOR_DARK_GREEN = (0, 90, 0)      # < 70 dB
COLOR_LIGHT_GREEN = (0, 255, 0)     # 70–85 dB
COLOR_YELLOW = (150,150, 0)        # 85–90 dB
COLOR_RED = (255, 0, 0)             # 95–102 dB
COLOR_ORANGE = (255, 128, 0)        # 90-95 dB
COLOR_BLACK = (0, 0, 0)             # for blinking
COLOR_BLUE = (0, 0, 255)            # peak


# ============================================================
# AUDIO CONFIG
# ============================================================
FS = 44100
CHUNK = 2048
window = np.ones(CHUNK) / CHUNK

# Averaging windows (in chunks)
FAST_WINDOW = 3          # ~125 ms
#SLOW_WINDOW = 22         # ~1 s
SLOW_WINDOW = 650         # ~30s
#MID_WINDOW = 1300        # ~60 s
MID_WINDOW = 6500       # ~5 min
LONG_WINDOW = 19380       # ~15 mins

MIN_DB=65
MAX_DB=105

fast_buffer = []
slow_buffer = []
mid_buffer = []
long_buffer = []
peak_long_value = 0


blink_state = False
last_blink = 0
last_info_log = time.time()


# ============================================================
# SPL CALIBRATION (placeholder)
# ============================================================
CALIBRATION_OFFSET = 132

# ============================================================
# ARGPARSE: --debug or --info
# ============================================================
parser = argparse.ArgumentParser(description="DJ Sonometer")
parser.add_argument("--debug", action="store_true", help="Enable debug logging")
args = parser.parse_args()

# Mode sélectionné
if args.debug:
    DEBUG = True
else:
    DEBUG = False  # default


# ============================================================
# LOGGER SETUP
# ============================================================

def rotate_log_startup(path: str):
    old_path = path + ".old"
    if os.path.exists(old_path):
        os.remove(old_path)
    if os.path.exists(path):
        shutil.move(path, old_path)

LOG_PATH = "sonometer.log"

# Rotate BEFORE creating handlers
rotate_log_startup(LOG_PATH)

logger = logging.getLogger("SonometerDJ")
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG if DEBUG else logging.INFO)

fh = logging.FileHandler(LOG_PATH)
fh.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
ch.setFormatter(formatter)
fh.setFormatter(formatter)

logger.addHandler(ch)
logger.addHandler(fh)

logger.info("Logger initialized (DEBUG=%s)", DEBUG)


# ============================================================
# CLEANUP
# ============================================================

def cleanup(signum, frame):
    try:
        logger.info("Cleanup triggered (signal=%s). Clearing display...", signum)
    except Exception:
        pass  # logger may not exist or may be shutting down

    try:
        clear()
        show()
    except Exception:
        pass  # avoid crash during shutdown

    try:
        logger.info("Display cleared. Exiting daemon.")
    except Exception:
        pass

    sys.exit(0)

signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)



# ============================================================
# AUDIO DEVICE CHECK
# ============================================================
def check_audio_device():
    try:
        devices = sd.query_devices()
        logger.info("Detected audio devices:")
        for i, d in enumerate(devices):
            logger.info("  %d : %s", i, d['name'])

        input_devices = [i for i, d in enumerate(devices) if d['max_input_channels'] > 0]

        if not input_devices:
            logger.error("No valid audio input device found!")
            return None
        
        device_index=99
        for i, d in enumerate(devices):
            if "USB" in d['name']:
                device_index = i
                break
        
        if device_index==99:
            logger.error("No valid USB audio input device found")
            return None
            
        sd.default.device = device_index
        logger.info("Selected audio device: %d (%s)", device_index, devices[device_index]['name'])
        return device_index

    except Exception as e:
        logger.error("Audio device detection error: %s", e)
        return None


# ============================================================
# UNICORN DISPLAY (your wording preserved)
# ============================================================
def draw_column(column_index, level, color):
    """Draw a full-height vertical bar at the given column index."""
    for x in range(level):
        draw_pixel( column_index, x+1,color)
        
def draw_pixel(column_index, row_index, color):
    """Draw a pixel at the given index."""
    uh.set_pixel(8 - row_index, 3-column_index, *color)


def compute_color_and_length(db):
    """Compute bar length and color using your DJ scale."""
    if db < MIN_DB:
        return 1, COLOR_DARK_GREEN

    db_clamped = max(MIN_DB, min(MAX_DB, db))
    length = max(1, int((db_clamped - MIN_DB) / (MAX_DB - MIN_DB) * 8))

    if db < 85:
        color = COLOR_LIGHT_GREEN
    elif db < 90:
        color = COLOR_YELLOW
    elif db < 95:
        color = COLOR_ORANGE
    elif db < 102:
        color = COLOR_RED
    else:
        global blink_state, last_blink
        now = time.time()
        if now - last_blink > 0.25:
            blink_state = not blink_state
            last_blink = now
        color = COLOR_RED if blink_state else COLOR_BLACK

    return length, color


def display_unicorn(fast_db, slow_db, mid_db, long_db):
    try:
        uh.clear()
        
        # FAST → columns 0
        fast_len, fast_color = compute_color_and_length(fast_db)
        draw_column(0, fast_len, fast_color)

        # SLOW → columns 1
        slow_len, slow_color = compute_color_and_length(slow_db)
        draw_column(1, slow_len, slow_color)

        # MID → columns 2
        mid_len, mid_color = compute_color_and_length(mid_db)
        draw_column(2, mid_len, mid_color)

        # LONG → columns 3
        long_len, long_color = compute_color_and_length(long_db)
        draw_column(3, long_len, long_color)
        
        # Blue LED for LONG peak on first 2 columns
        if peak_long_value > 0:
            peak_length,peak_color = compute_color_and_length(peak_long_value)
            draw_pixel(0, peak_length, COLOR_BLUE)

        uh.show()

        logger.debug(
            "Display FAST=%.1f dB, SLOW=%.1f dB, MID=%.1f dB, LONG=%.1f dB, PEAK=%.1f dB",
            fast_db, slow_db, mid_db, long_db,peak_long_value
        )

    except Exception as e:
        logger.error("Unicorn pHAT error: %s", e)
        raise


# ============================================================
# MEASURE SPL
# ============================================================
def measure_db():
    try:
        audio = sd.rec(CHUNK, samplerate=FS, channels=1, blocking=True)
        rms = np.sqrt(np.sum((audio[:, 0] ** 2) * window))
        dbfs = 20 * np.log10(rms + 1e-12)
        return dbfs + CALIBRATION_OFFSET
    except Exception as e:
        logger.error("Audio measurement error: %s", e)
        return 0


# ============================================================
# MAIN LOOP
# ============================================================
logger.info("DJ Sonometer started…")

uh.set_layout(uh.PHAT)
uh.brightness(0.5)

device = check_audio_device()
if device is None:
    logger.error("Startup aborted: no valid audio device.")
    exit(1)

while True:
    try:
        spl = measure_db()

        # FAST
        fast_buffer.append(spl)
        if len(fast_buffer) > FAST_WINDOW:
            fast_buffer.pop(0)
        fast_db = np.mean(fast_buffer)

        # SLOW
        slow_buffer.append(spl)
        if len(slow_buffer) > SLOW_WINDOW:
            slow_buffer.pop(0)
        slow_db = np.mean(slow_buffer)

        # MID 
        mid_buffer.append(spl)
        if len(mid_buffer) > MID_WINDOW:
            mid_buffer.pop(0)
        mid_db = np.mean(mid_buffer)

        # LONG
        long_buffer.append(spl)
        if len(long_buffer) > LONG_WINDOW:
            long_buffer.pop(0)
        long_db = np.mean(long_buffer)
        
        #DEBUG
        #slow_db=72
        
        
        # Peak LONG = maximum on last 5 minutes
        # We wait a while before showing peak because sometimes weird value at startup
        if len(slow_buffer) > 20:
            peak_long_value = max(peak_long_value, np.max(fast_buffer))
        
        display_unicorn(fast_db, slow_db, mid_db, long_db)
        
        # INFO logs only once per second
        if not DEBUG:
            now = time.time()
            if now - last_info_log >= 1.0:
                logger.info(
                    "FAST=%.1f dB | SLOW=%.1f dB | MID=%.1f dB | LONG=%.1f dB | PEAK=%.1f dB",
                    fast_db, slow_db, mid_db, long_db, peak_long_value
                )
                last_info_log = now


    except KeyboardInterrupt:
        logger.info("Manual stop by user")
        break
    except Exception as e:
        logger.error("Main loop error: %s", e)
        raise
