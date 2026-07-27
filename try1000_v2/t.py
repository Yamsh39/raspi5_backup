from picamera2 import Picamera2
import cv2
import os

SAVE_PATH = "/home/pi/Documents/try1000_v2/image.jpg"

picam2 = Picamera2()

config = picam2.create_preview_configuration(
    main={"size": (640, 480)}
)

picam2.configure(config)
picam2.start()

frame = picam2.capture_array()

success, jpg = cv2.imencode(
    ".jpg",
    frame,
    [cv2.IMWRITE_JPEG_QUALITY, 80]
)

if success:
    with open(SAVE_PATH, "wb") as f:
        f.write(jpg.tobytes())

    size = os.path.getsize(SAVE_PATH)
    print(f"Saved: {SAVE_PATH}")
    print(f"File Size: {size} bytes")
else:
    print("JPEG Encode Failed")