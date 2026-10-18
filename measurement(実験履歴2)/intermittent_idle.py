from picamera2 import Picamera2
import cv2
import requests
import time

CYCLES = 5  # 測定する周期数
WARMUP = 1  # 平均から除外する最初の測定回数
TEST_COUNT = WARMUP + CYCLES

PERIOD_MS = 180000  # 周期 [ms]（撮影開始〜次の撮影開始）
FRAME_PERIOD = PERIOD_MS / 1000

ENABLE_CAPTURE = True
ENABLE_JPEG = True
ENABLE_WIFI = True

SERVER_URL = "http://192.168.3.15:3000/upload"
IMAGE_PATH = "/home/pi/Documents/image.jpg"


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
        main={"size": (640, 480), "format": "RGB888"}
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

capture_total = 0.0
jpeg_total = 0.0
wifi_total = 0.0
all_total = 0.0
valid_count = 0
missed_deadline = 0

for i in range(TEST_COUNT):

    # 測定区間の開始マーカー（電力ログの目印）
    if i == WARMUP:
        print("---- start marker ----")
        cpu_marker()

    # フレーム開始時刻
    frame_start = time.perf_counter()

    frame = None
    jpg = None

    t0 = time.perf_counter()

    # 撮影
    if ENABLE_CAPTURE:
        frame = picam2.capture_array()

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

    # 周期制御（間欠動作・アイドル待機）
    elapsed = time.perf_counter() - frame_start
    remaining = FRAME_PERIOD - elapsed

    if remaining > 0:
        time.sleep(remaining)
    else:
        missed_deadline += 1

# 測定区間の終了マーカー
print("---- end marker ----")
cpu_marker()

print(f"\n===== Average (excluding first {WARMUP} runs) =====")
print(f"Period  : {PERIOD_MS} ms")
print(f"Capture : {capture_total / valid_count:.2f} ms")
print(f"JPEG    : {jpeg_total / valid_count:.2f} ms")
print(f"WiFi    : {wifi_total / valid_count:.2f} ms")
print(f"Total   : {all_total / valid_count:.2f} ms")
print(f"missed  : {missed_deadline:d}")