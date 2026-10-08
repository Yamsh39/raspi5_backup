from picamera2 import Picamera2
import cv2
import requests
import time

TEST_COUNT = 105
WARMUP = 5  # 平均から除外する最初の測定回数

ENABLE_CAPTURE = False
ENABLE_JPEG = True
ENABLE_WIFI = False

SERVER_URL = "http://192.168.3.7:3000/upload"
IMAGE_PATH = "/home/pi/Documents/check_each_time/image.jpg"


def cpu_marker(duration=2.0):
    end = time.perf_counter() + duration
    x = 0
    while time.perf_counter() < end:
        x += 1
        x *= 2
        x //= 2


fixed_jpg = None

if ENABLE_WIFI and not ENABLE_JPEG:
    with open(IMAGE_PATH, "rb") as f:
        fixed_jpg = f.read()

fixed_frame = None

if ENABLE_JPEG and not ENABLE_CAPTURE:
    fixed_frame = cv2.imread(IMAGE_PATH)


if ENABLE_CAPTURE:
    picam2 = Picamera2()

    config = picam2.create_preview_configuration(
        main={"size": (640, 480)}
    )

    picam2.configure(config)
    picam2.start()

    # カメラ・JPEGのウォームアップ
    for _ in range(10):
        frame = picam2.capture_array()
        cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 80]
    )

cpu_marker(2.0)

capture_total = 0.0
jpeg_total = 0.0
wifi_total = 0.0
all_total = 0.0
valid_count = 0

for i in range(TEST_COUNT):

    frame = None
    jpg = None

    t0 = time.perf_counter()

    # 撮影
    if ENABLE_CAPTURE:
        frame = picam2.capture_array()
    else:
        frame = fixed_frame

    t1 = time.perf_counter()

    # JPEG変換
    if ENABLE_JPEG:
        success, jpg = cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 80]
        )

        if not success:
            continue

    t2 = time.perf_counter()

    # Wi-Fi送信
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

    t3 = time.perf_counter()

    capture_ms = (t1 - t0) * 1000
    jpeg_ms = (t2 - t1) * 1000
    wifi_ms = (t3 - t2) * 1000
    total_ms = (t3 - t0) * 1000

    print(
        f"{i+1:2d}: "
        f"Capture={capture_ms:7.2f} ms  "
        f"JPEG={jpeg_ms:7.2f} ms  "
        f"WiFi={wifi_ms:7.2f} ms  "
        f"Total={total_ms:7.2f} ms"
    )

    # 最初のWARMUP回は平均から除外
    if i >= WARMUP:
        capture_total += capture_ms
        jpeg_total += jpeg_ms
        wifi_total += wifi_ms
        all_total += total_ms
        valid_count += 1

cpu_marker(2.0)

print(f"\n===== Average (excluding first {WARMUP} runs) =====")
print(f"Capture : {capture_total / valid_count:.2f} ms")
print(f"JPEG    : {jpeg_total / valid_count:.2f} ms")
print(f"WiFi    : {wifi_total / valid_count:.2f} ms")
print(f"Total   : {all_total / valid_count:.2f} ms")