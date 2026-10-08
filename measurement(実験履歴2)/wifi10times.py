from picamera2 import Picamera2
import cv2
import requests
import time

TEST_COUNT = 10

ENABLE_CAPTURE = False
ENABLE_JPEG = False
ENABLE_WIFI = True

SERVER_URL = "http://192.168.3.13:3000/upload"
IMAGE_PATH = "/home/pi/Documents/try1000_v2/image.jpg"

def cpu_marker(duration=2.0):
    end = time.perf_counter() + duration
    x = 0
    while time.perf_counter() < end:
        x += 1
        x *= 2
        x //= 2

if ENABLE_WIFI and not ENABLE_CAPTURE:
    with open(IMAGE_PATH, "rb") as f:
        fixed_jpg = f.read()

if ENABLE_CAPTURE:
    picam2 = Picamera2()

    config = picam2.create_preview_configuration(
        main={"size": (640, 480)}
    )

    picam2.configure(config)
    picam2.start()
    for _ in range(10):
        picam2.capture_array()

cpu_marker(2.0)

start = time.perf_counter()

for i in range(TEST_COUNT):

    # 撮影有効化
    if ENABLE_CAPTURE:
        frame = picam2.capture_array()

    # JPEG変換有効化
    if ENABLE_JPEG:
        success, jpg = cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 80]
        )

        if not success:
            continue

    # Wifi有効化
    if ENABLE_WIFI:
        if ENABLE_JPEG:
            send_data = jpg.tobytes()
        else:
            send_data = fixed_jpg[:]

        requests.post(
            SERVER_URL,
            data=send_data,
            headers={
                "Content-Type": "image/jpeg"
            }
        )

end = time.perf_counter()

cpu_marker(2.0)

avg_ms = (end - start) * 1000 / TEST_COUNT

print(f"Average Processing Time = {avg_ms:.3f} ms")