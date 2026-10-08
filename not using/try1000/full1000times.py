from picamera2 import Picamera2
import cv2
import requests
import time

TEST_COUNT = 1000

picam2 = Picamera2()

config = picam2.create_preview_configuration(
    main={"size": (640, 480)}
)

picam2.configure(config)
picam2.start()

start = time.perf_counter()

for i in range(TEST_COUNT):
    frame = picam2.capture_array()

    success, jpg = cv2.imencode(
        ".jpg",
        frame,
        [cv2.IMWRITE_JPEG_QUALITY, 80]
    )

    if not success:
        print(f"JPEG Encode Failed: {i}")
        continue

    requests.post(
        "http://192.168.3.5:3000/upload",
        data=jpg.tobytes(),
        headers={
            "Content-Type": "image/jpeg"
        }
    )

end = time.perf_counter()

avg_ms = (end - start) * 1000 / TEST_COUNT

print(
    f"Average Capture + JPEG + WiFi Time = {avg_ms:.3f} ms"
)