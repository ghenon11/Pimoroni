import time
import unicornhat as uh
import logging
import sounddevice as sd
import numpy as np

# ============================================================
# DJ COLOR SCALE
# ============================================================
COLOR_DARK_GREEN = (0, 100, 0)      # < 70 dB
COLOR_LIGHT_GREEN = (0, 255, 0)    # 70–85 dB
COLOR_YELLOW = (255, 255, 0)       # 85–95 dB
COLOR_RED = (255, 0, 0)            # 95–102 dB
COLOR_BLACK = (0, 0, 0)            # blinking red

# ============================================================
# AUDIO CONFIG
# ============================================================
FS = 44100
CHUNK = 2048
window = np.ones(CHUNK) / CHUNK

blink_state = False
last_blink = 0

# ============================================================
# SPL CALIBRATION (placeholder)
# ============================================================
CALIBRATION_OFFSET = 0.0   # We will adjust this after comparing with your mobile app

# ============================================================
# DEBUG MODE
# ============================================================
DEBUG = True

# ============================================================
# LOGGER SETUP
# ============================================================
logger = logging.getLogger("SonometerDJ")
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG if DEBUG else logging.INFO)

fh = logging.FileHandler("sonometer.log")
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
# AUDIO DEVICE CHECK
# ============================================================
def check_audio_device():
    """Detect and select a valid audio input device."""
    try:
        devices = sd.query_devices()
        logger.info("Detected audio devices:")
        for i, d in enumerate(devices):
            logger.info("  %d : %s", i, d['name'])

        input_devices = [i for i, d in enumerate(devices) if d['max_input_channels'] > 0]

        if not input_devices:
            logger.error("No valid audio input device found!")
            return None

        device_index = input_devices[0]
        sd.default.device = device_index
        logger.info("Selected audio device: %d (%s)", device_index, devices[device_index]['name'])
        return device_index

    except Exception as e:
        logger.error("Audio device detection error: %s", e)
        return None


# ============================================================
# UNICORN DISPLAY
# ============================================================
def display_unicorn(db):
    """Display SPL level using DJ color scale."""
    global blink_state, last_blink

    try:
        uh.clear()

        # Special case: < 70 dB → top row dark green
        if db < 70:
            for y in range(4):
                uh.set_pixel(7, y, *COLOR_DARK_GREEN)
            uh.show()
            logger.debug("Display <70 dB: dark green")
            return

        # Normalize 70–115 dB → 0–8 LEDs
        db_clamped = max(70, min(115, db))
        length = int((db_clamped - 70) / (115 - 70) * 8)

        # Select color based on DJ scale
        if db < 85:
            color = COLOR_LIGHT_GREEN
        elif db < 95:
            color = COLOR_YELLOW
        elif db < 102:
            color = COLOR_RED
        else:
            # Blinking red > 102 dB
            now = time.time()
            if now - last_blink > 0.25:
                blink_state = not blink_state
                last_blink = now
            color = COLOR_RED if blink_state else COLOR_BLACK

        # Draw bar on bottom row
        for x in range(length):
            for y in range(4)
                uh.set_pixel(7-x, y, *color)

        uh.show()
        logger.debug("Unicorn display OK: db=%.1f, LEDs=%d", db, length)

    except Exception as e:
        logger.error("Unicorn pHAT error: %s", e)


# ============================================================
# MEASURE SPL (pre‑calibration)
# ============================================================
def measure_db():
    """
    Record audio, compute RMS, convert to dBFS,
    then apply calibration offset (later).
    """
    try:
        audio = sd.rec(CHUNK, samplerate=FS, channels=1, blocking=True)

        # Basic RMS (no A-weighting yet)
        rms = np.sqrt(np.sum((audio[:, 0] ** 2) * window))

        # Convert to digital dBFS
        dbfs = 20 * np.log10(rms + 1e-12)

        # Apply calibration offset (we will adjust this later)
        spl = dbfs + CALIBRATION_OFFSET

        logger.debug("Measured SPL (pre-calibration): %.2f dB", spl)
        return spl

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
        db = measure_db()
        display_unicorn(db)
    except KeyboardInterrupt:
        logger.info("Manual stop by user")
        break
    except Exception as e:
        logger.error("Main loop error: %s", e)
