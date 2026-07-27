from picamera2 import Picamera2
import cv2
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

    # 撮影
    frame = picam2.capture_array()

    # JPEG変換
    success, jpg = cv2.imencode(
        ".jpg",
        frame,
        [cv2.IMWRITE_JPEG_QUALITY, 80]
    )

    if not success:
        print(f"JPEG Encode Failed: {i}")

end = time.perf_counter()

avg_ms = (end - start) * 1000 / TEST_COUNT

print(
    f"Average Capture + JPEG Time = {avg_ms:.3f} ms"
)