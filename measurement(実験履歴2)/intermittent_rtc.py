from picamera2 import Picamera2
import cv2
import requests
import time
import json
import os
import sys
import subprocess

CYCLES = 10  # 測定する周期数
WARMUP = 1  # 平均から除外する最初の周期数（タイマー起動では1周期＝起動1回）

PERIOD_MS = 60000 # 周期 [ms]（RTC起動時刻〜次のRTC起動時刻）。RTCは1秒単位
FRAME_PERIOD = PERIOD_MS / 1000

SHUTDOWN_MARGIN = 15  # 電源が落ちきるまでの余裕 [s]。次の起動時刻がこれより近いと周期に間に合わない扱い

ENABLE_CAPTURE = True
ENABLE_JPEG = True
ENABLE_WIFI = True

SERVER_URL = "http://192.168.3.15:3000/upload"
IMAGE_PATH = "/home/pi/Documents/image.jpg"

BASE_DIR = "/home/pi/Documents/measurement(実験履歴2)"
STATE_PATH = BASE_DIR + "/rtc_state.json"  # 何周期目か・次の起動時刻を起動をまたいで保存
LOG_PATH = BASE_DIR + f"/rtc_{PERIOD_MS}ms.csv"
RTC_WAKEALARM = "/sys/class/rtc/rtc0/wakealarm"


def cpu_marker(duration=2.0):
    end = time.perf_counter() + duration
    x = 0
    while time.perf_counter() < end:
        x += 1
        x *= 2
        x //= 2


def set_alarm_and_halt(wake_epoch):
    # RTCに次の起動時刻をセットして電源を落とす（root権限が必要）
    with open(RTC_WAKEALARM, "w") as f:
        f.write("0")
    with open(RTC_WAKEALARM, "w") as f:
        f.write(str(int(wake_epoch)))
    subprocess.run(["halt"])


# ===== 測定開始（手動で1回だけ実行：sudo python3 rpi5_rtc.py start）=====
if len(sys.argv) > 1 and sys.argv[1] == "start":
    first_wake = int(time.time()) + 30  # 30秒後に1周期目を起動
    with open(STATE_PATH, "w") as f:
        json.dump({"cycle": 0, "next_wake": first_wake, "missed": 0}, f)
    with open(LOG_PATH, "w") as f:
        f.write("cycle,measured,wake_ms,capture_ms,jpeg_ms,wifi_ms,total_ms,missed\n")
    print(f"start: period {PERIOD_MS} ms, first wake in 30 s")
    set_alarm_and_halt(first_wake)
    sys.exit()

# ===== 起動ごとに実行（systemdから呼ばれる）=====
if not os.path.exists(STATE_PATH):
    sys.exit()  # 測定中でなければ何もしない

with open(STATE_PATH) as f:
    state = json.load(f)

slot_start = state["next_wake"]  # この周期の開始時刻＝RTCで起動した時刻
cycle = state["cycle"] + 1

# 全周期が終わった後の起動：終了マーカーを出して結果を表示（電源は入れたまま）
if cycle > WARMUP + CYCLES:
    print("---- end marker ----")
    cpu_marker()

    rows = []
    with open(LOG_PATH) as f:
        next(f)
        for line in f:
            v = line.strip().split(",")
            if v[1] == "1":
                rows.append([float(x) for x in v[2:7]])
    n = len(rows)
    print(f"\n===== Average (excluding first {WARMUP} runs) =====")
    print(f"Period  : {PERIOD_MS} ms")
    print(f"Wake    : {sum(r[0] for r in rows) / n:.2f} ms")
    print(f"Capture : {sum(r[1] for r in rows) / n:.2f} ms")
    print(f"JPEG    : {sum(r[2] for r in rows) / n:.2f} ms")
    print(f"WiFi    : {sum(r[3] for r in rows) / n:.2f} ms")
    print(f"Total   : {sum(r[4] for r in rows) / n:.2f} ms")
    print(f"missed  : {state['missed']:d}")

    os.remove(STATE_PATH)
    sys.exit()

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

    # カメラ・JPEGのウォームアップ（毎回の起動で必要なので復帰時間に含まれる）
    for _ in range(10):
        frame = picam2.capture_array()
        cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 80]
        )

frame = None
jpg = None

# 復帰時間：RTCで起動した時刻から撮影開始まで（起動・Wi-Fi接続・カメラ準備）
wake_ms = (time.time() - slot_start) * 1000

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

# 次の起動時刻。電源が落ちきる前に来てしまう場合は次の周期に回す
next_wake = slot_start + FRAME_PERIOD
missed = 0
while next_wake < time.time() + SHUTDOWN_MARGIN:
    next_wake += FRAME_PERIOD
    missed = 1

measured = 1 if cycle > WARMUP else 0

with open(LOG_PATH, "a") as f:
    f.write(
        f"{cycle},{measured},{wake_ms:.2f},{capture_ms:.2f},{jpeg_ms:.2f},"
        f"{wifi_ms:.2f},{total_ms:.2f},{missed}\n"
    )

state["cycle"] = cycle
state["next_wake"] = next_wake
state["missed"] += missed * measured
with open(STATE_PATH, "w") as f:
    json.dump(state, f)

set_alarm_and_halt(next_wake)
