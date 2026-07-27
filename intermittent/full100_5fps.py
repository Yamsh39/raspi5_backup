from picamera2 import Picamera2
import cv2
import requests
import time

TARGET_FPS = 5
FRAME_PERIOD = 1.0 / TARGET_FPS
MEASURE_TIME = 100

picam2 = Picamera2()

config = picam2.create_preview_configuration(
    main={"size": (640, 480)}
)

picam2.configure(config)
picam2.start()

start = time.perf_counter()

frame_count = 0
total_processing = 0

while time.perf_counter() - start < MEASURE_TIME:

    frame_start = time.perf_counter()

    frame = picam2.capture_array()

    success, jpg = cv2.imencode(
        ".jpg",
        frame,
        [cv2.IMWRITE_JPEG_QUALITY, 80]
    )

    if success:
        requests.post(
            "http://192.168.3.15:3000/upload",
            data=jpg.tobytes(),
            headers={
                "Content-Type": "image/jpeg"
            }
        )

    frame_end = time.perf_counter()

    processing = frame_end - frame_start

    total_processing += processing
    frame_count += 1

    if processing < FRAME_PERIOD:
        time.sleep(FRAME_PERIOD - processing)

end = time.perf_counter()

avg_ms = (
    total_processing * 1000 / frame_count
)

print("Frames =", frame_count)
print("Total Time =", end-start)
print("Average Processing Time =", avg_ms)
print("Average FPS =", frame_count/(end-start))