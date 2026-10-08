from picamera2 import Picamera2
import cv2
import requests
import time

TEST_COUNT = 1000

ENABLE_CAPTURE = True
ENABLE_JPEG = True
ENABLE_WIFI = True

SERVER_URL = "http://192.168.3.13:3000/upload"
IMAGE_PATH = "./image.jpg"


def cpu_marker(duration=2.0):
    end = time.perf_counter() + duration
    x = 0
    while time.perf_counter() < end:
        x += 1
        x *= 2
        x //= 2


# --------------------------------------------------
# カメラ初期化（Wi-Fiのみでも1枚撮影するため初期化）
# --------------------------------------------------
picam2 = Picamera2()

config = picam2.create_preview_configuration(
    main={"size": (640, 480)}
)

picam2.configure(config)
picam2.start()

# カメラ安定化
for _ in range(10):
    picam2.capture_array()

# --------------------------------------------------
# Wi-Fiのみの場合は1枚だけ撮影して保存
# --------------------------------------------------
if ENABLE_WIFI and not ENABLE_CAPTURE:

    frame = picam2.capture_array()

    success, jpg = cv2.imencode(
        ".jpg",
        frame,
        [cv2.IMWRITE_JPEG_QUALITY, 80]
    )

    if not success:
        raise RuntimeError("JPEG encode failed")

    with open(IMAGE_PATH, "wb") as f:
        f.write(jpg.tobytes())

    with open(IMAGE_PATH, "rb") as f:
        fixed_jpg = f.read()

cpu_marker(2.0)

capture_total = 0.0
jpeg_total = 0.0
wifi_total = 0.0
all_total = 0.0

for i in range(TEST_COUNT):

    frame = None
    jpg = None

    t0 = time.perf_counter()

    # ---------------- Capture ----------------
    if ENABLE_CAPTURE:
        frame = picam2.capture_array()
        metadata = picam2.capture_metadata()
        print(metadata)

    t1 = time.perf_counter()

    # ---------------- JPEG ----------------
    if ENABLE_JPEG:
        success, jpg = cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 80]
        )

        if not success:
            continue

    t2 = time.perf_counter()

    # ---------------- Wi-Fi ----------------
    if ENABLE_WIFI:

        if ENABLE_JPEG:
            send_data = jpg.tobytes()
        else:
            send_data = fixed_jpg

        requests.post(
            SERVER_URL,
            data=send_data,
            headers={
                "Content-Type": "image/jpeg"
            }
        )

    t3 = time.perf_counter()

    capture_ms = (t1 - t0) * 1000
    jpeg_ms = (t2 - t1) * 1000
    wifi_ms = (t3 - t2) * 1000
    total_ms = (t3 - t0) * 1000

    capture_total += capture_ms
    jpeg_total += jpeg_ms
    wifi_total += wifi_ms
    all_total += total_ms

cpu_marker(2.0)

print("\n===== Average =====")
print(f"Capture : {capture_total / TEST_COUNT:.3f} ms")
print(f"JPEG    : {jpeg_total / TEST_COUNT:.3f} ms")
print(f"WiFi    : {wifi_total / TEST_COUNT:.3f} ms")
print(f"Total   : {all_total / TEST_COUNT:.3f} ms")