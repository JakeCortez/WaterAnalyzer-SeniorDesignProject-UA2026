import subprocess
import cv2
import numpy as np
import math
from gpiozero import LED

# ----------------------------
# Settings
# ----------------------------
preview_width = 640
preview_height = 640
lens_position = 15
min_area = 80
center_square_size = 20

# LED pins
led1 = LED(27)
led2 = LED(22)

# Optional ROI for searching in live frame
search_roi = None
# search_roi = [100, 80, 440, 300]

# ----------------------------
# Calibration equations
# ----------------------------
# Nitrate:    A = 2.68E-03*x - 0.0317
# Phosphate:  A = 2.58E-03*x + 0.00629

NITRATE_SLOPE = 2.68e-3
NITRATE_INTERCEPT = -0.0317

PHOSPHATE_SLOPE = 2.58e-3
PHOSPHATE_INTERCEPT = 0.00629

# ----------------------------
# 0 ppm baseline intensities
# ----------------------------
# Nitrate uses GREEN channel from the RED pad
# Phosphate uses RED channel from the BLUE pad
NITRATE_I0_GREEN = 152.0
PHOSPHATE_I0_RED = 135.0

# ----------------------------
# Helper functions
# ----------------------------
def clean_mask(mask):
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask

def find_best_box(mask, min_area=80):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    best_box = None
    best_score = -1

    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area:
            continue

        x, y, w, h = cv2.boundingRect(c)
        roi = mask[y:y+h, x:x+w]
        white_pixels = cv2.countNonZero(roi)

        if white_pixels > best_score:
            best_score = white_pixels
            best_box = (x, y, w, h)

    return best_box

def clamp_box(x, y, w, h, frame_w, frame_h):
    x = max(0, x)
    y = max(0, y)
    w = max(1, w)
    h = max(1, h)

    if x + w > frame_w:
        w = frame_w - x
    if y + h > frame_h:
        h = frame_h - y

    return x, y, w, h

def get_center_square(box_w, box_h, square_size):
    cx = box_w // 2
    cy = box_h // 2
    half = square_size // 2

    x = max(0, cx - half)
    y = max(0, cy - half)
    w = min(square_size, box_w - x)
    h = min(square_size, box_h - y)

    return x, y, w, h

def mean_rgb_from_bgr_roi(roi):
    mean_bgr = cv2.mean(roi)[:3]
    return (
        float(mean_bgr[2]),  # R
        float(mean_bgr[1]),  # G
        float(mean_bgr[0])   # B
    )

def compute_absorbance(I, I0):
    I = max(I, 1e-6)
    I0 = max(I0, 1e-6)
    return -math.log10(I / I0)

def absorbance_to_ppm(absorbance, slope, intercept):
    if abs(slope) < 1e-12:
        return None
    return (absorbance - intercept) / slope

def ppm_to_bin(ppm, step=10, max_ppm=100):
    if ppm is None:
        return "Invalid"

    if ppm < 0:
        return "Below 0 ppm"

    if ppm > max_ppm:
        return f"Above {max_ppm} ppm"

    lower = int(ppm // step) * step
    upper = lower + step

    if ppm == max_ppm:
        lower = max_ppm - step
        upper = max_ppm

    return f"{lower}-{upper} ppm"

# ----------------------------
# Start camera stream (MANUAL FOCUS)
# ----------------------------
def analysis():
    cmd = [
        "rpicam-vid",
        "--timeout", "0",
        "--width", str(preview_width),
        "--height", str(preview_height),
        "--framerate", "30",
        "--codec", "mjpeg",
        "--output", "-",
        "--nopreview",
        "--autofocus-mode", "manual",
        "--lens-position", str(lens_position)
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0
    )

    print("Live feed running...")
    print("Press ENTER to capture and analyze pads.")
    print("Press 'q' to quit.")

    led1.on()
    led2.on()

    buffer = b""
    capture_count = 1

    try:
        while True:
            chunk = process.stdout.read(4096)

            if not chunk:
                err = process.stderr.read().decode("utf-8", errors="ignore")
                print("No camera data received.")
                print(err)
                break

            buffer += chunk

            start = buffer.find(b'\xff\xd8')
            end = buffer.find(b'\xff\xd9')

            if start != -1 and end != -1 and end > start:
                jpg = buffer[start:end + 2]
                buffer = buffer[end + 2:]

                frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                if frame is None:
                    continue

                display = frame.copy()

                # ----------------------------
                # ROI handling
                # ----------------------------
                if search_roi is not None:
                    sx, sy, sw, sh = search_roi
                    search_img = frame[sy:sy+sh, sx:sx+sw]
                    cv2.rectangle(display, (sx, sy), (sx+sw, sy+sh), (0, 255, 255), 2)
                else:
                    sx, sy = 0, 0
                    search_img = frame

                hsv = cv2.cvtColor(search_img, cv2.COLOR_BGR2HSV)

                # ----------------------------
                # RED / LIGHT PINK detection
                # ----------------------------
                lower_red1 = np.array([145, 70, 40])
                upper_red1 = np.array([170, 255, 220])

                lower_red2 = np.array([0, 70, 40])
                upper_red2 = np.array([10, 255, 220])

                red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
                red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
                red_mask = clean_mask(cv2.bitwise_or(red_mask1, red_mask2))

                # ----------------------------
                # BLUE detection
                # ----------------------------
                lower_blue = np.array([95, 80, 40])
                upper_blue = np.array([125, 255, 220])
                blue_mask = clean_mask(cv2.inRange(hsv, lower_blue, upper_blue))

                # Debug masks
                cv2.imshow("Red Mask", red_mask)
                cv2.imshow("Blue Mask", blue_mask)

                # ----------------------------
                # Find strongest regions
                # ----------------------------
                red_box = find_best_box(red_mask, min_area)
                blue_box = find_best_box(blue_mask, min_area)

                full_red_box = None
                full_blue_box = None

                if red_box is not None:
                    x, y, w, h = red_box
                    x += sx
                    y += sy
                    full_red_box = (x, y, w, h)
                    cv2.rectangle(display, (x, y), (x+w, y+h), (0, 0, 255), 3)
                    cv2.putText(display, "NITRATE PAD", (x, y-10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

                if blue_box is not None:
                    x, y, w, h = blue_box
                    x += sx
                    y += sy
                    full_blue_box = (x, y, w, h)
                    cv2.rectangle(display, (x, y), (x+w, y+h), (255, 0, 0), 3)
                    cv2.putText(display, "PHOSPHATE PAD", (x, y-10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

                cv2.imshow("Live Detection", display)
                key = cv2.waitKey(1) & 0xFF

                # ----------------------------
                # Capture and analyze
                # ----------------------------
                if key == 13 or key == 10:
                    print(f"\n--- Capture {capture_count} ---")

                    captured_display = display.copy()
                    captured_frame = frame.copy()

                    cv2.imshow("Captured Image", captured_display)

                    # Default results
                    nitrate_bin = "Not detected"
                    phosphate_bin = "Not detected"

                    # ----------------------------
                    # NITRATE = RED PAD, use GREEN channel
                    # ----------------------------
                    if full_red_box is not None:
                        rx, ry, rw, rh = clamp_box(*full_red_box, captured_frame.shape[1], captured_frame.shape[0])
                        red_crop = captured_frame[ry:ry+rh, rx:rx+rw].copy()

                        csx, csy, csw, csh = get_center_square(
                            red_crop.shape[1],
                            red_crop.shape[0],
                            center_square_size
                        )

                        red_center = red_crop[csy:csy+csh, csx:csx+csw]
                        red_r, red_g, red_b = mean_rgb_from_bgr_roi(red_center)

                        nitrate_abs = compute_absorbance(red_g, NITRATE_I0_GREEN)
                        nitrate_ppm = absorbance_to_ppm(
                            nitrate_abs,
                            NITRATE_SLOPE,
                            NITRATE_INTERCEPT
                        )
                        nitrate_bin = ppm_to_bin(nitrate_ppm)

                        cv2.rectangle(red_crop, (csx, csy), (csx+csw, csy+csh), (0, 255, 255), 2)
                        cv2.putText(red_crop, f"RGB: ({red_r:.1f}, {red_g:.1f}, {red_b:.1f})", (5, 20),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 2)
                        cv2.putText(red_crop, f"Nitrate: {nitrate_bin}", (5, 45),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 2)

                        cv2.imshow("Red ROI Capture", red_crop)

                        print(f"RED PAD RGB: ({red_r:.2f}, {red_g:.2f}, {red_b:.2f})")
                        print(f"Nitrate absorbance (GREEN): {nitrate_abs:.4f}")
                        print(f"Nitrate estimated ppm: {nitrate_ppm:.2f}")
                        print(f"Nitrate bin: {nitrate_bin}")
                    else:
                        print("RED PAD not detected.")

                    # ----------------------------
                    # PHOSPHATE = BLUE PAD, use RED channel
                    # ----------------------------
                    if full_blue_box is not None:
                        bx, by, bw, bh = clamp_box(*full_blue_box, captured_frame.shape[1], captured_frame.shape[0])
                        blue_crop = captured_frame[by:by+bh, bx:bx+bw].copy()

                        csx, csy, csw, csh = get_center_square(
                            blue_crop.shape[1],
                            blue_crop.shape[0],
                            center_square_size
                        )

                        blue_center = blue_crop[csy:csy+csh, csx:csx+csw]
                        blue_r, blue_g, blue_b = mean_rgb_from_bgr_roi(blue_center)

                        phosphate_abs = compute_absorbance(blue_r, PHOSPHATE_I0_RED)
                        phosphate_ppm = absorbance_to_ppm(
                            phosphate_abs,
                            PHOSPHATE_SLOPE,
                            PHOSPHATE_INTERCEPT
                        )
                        phosphate_bin = ppm_to_bin(phosphate_ppm)

                        cv2.rectangle(blue_crop, (csx, csy), (csx+csw, csy+csh), (0, 255, 255), 2)
                        cv2.putText(blue_crop, f"RGB: ({blue_r:.1f}, {blue_g:.1f}, {blue_b:.1f})", (5, 20),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 2)
                        cv2.putText(blue_crop, f"Phosphate: {phosphate_bin}", (5, 45),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 2)

                        cv2.imshow("Blue ROI Capture", blue_crop)

                        print(f"BLUE PAD RGB: ({blue_r:.2f}, {blue_g:.2f}, {blue_b:.2f})")
                        print(f"Phosphate absorbance (RED): {phosphate_abs:.4f}")
                        print(f"Phosphate estimated ppm: {phosphate_ppm:.2f}")
                        print(f"Phosphate bin: {phosphate_bin}")
                    else:
                        print("BLUE PAD not detected.")

                    # ----------------------------
                    # Show both results on full captured image
                    # ----------------------------
                    result_img = captured_display.copy()
                    cv2.putText(result_img, f"Nitrate: {nitrate_bin}", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    cv2.putText(result_img, f"Phosphate: {phosphate_bin}", (10, 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

                    cv2.imshow("Results", result_img)

                    filename = f"captured_frame_{capture_count}.png"
                    cv2.imwrite(filename, result_img)
                    print("Saved result image as:", filename)

                    capture_count += 1

                elif key == ord('q'):
                    break

    finally:
        if process.poll() is None:
            process.terminate()
            process.wait()

        led1.off()
        led2.off()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    analysis()