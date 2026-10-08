from picamera2 import Picamera2
import cv2
import time

picam2 = Picamera2()

config = picam2.create_preview_configuration(
    main={"size": (640, 480)}
)

picam2.start()

# ウォームアップ
for _ in range(10):
    picam2.capture_array()

t1 = time.perf_counter()
frame = picam2.capture_array()
t2 = time.perf_counter()

success, jpg = cv2.imencode(
    ".jpg",
    frame,
    [cv2.IMWRITE_JPEG_QUALITY, 80]
)
t3 = time.perf_counter()

print(f"Capture : {(t2-t1)*1000:.3f} ms")
print(f"JPEG    : {(t3-t2)*1000:.3f} ms")
print(f"Total   : {(t3-t1)*1000:.3f} ms")