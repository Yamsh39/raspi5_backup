from picamera2 import Picamera2
import time

FRAME_COUNT = 30

picam2 = Picamera2()

config = picam2.create_preview_configuration(
    main={"size": (640, 480)}
)

picam2.configure(config)
picam2.start()

# ウォームアップ
for _ in range(10):
    picam2.capture_array()

print("Frame | Capture(ms) | Metadata(ms) | SensorTimestamp")
print("-" * 70)

capture_sum = 0
metadata_sum = 0

for i in range(FRAME_COUNT):

    # capture_array() の時間
    t0 = time.perf_counter()
    frame = picam2.capture_array()
    t1 = time.perf_counter()

    # capture_metadata() の時間
    metadata = picam2.capture_metadata()
    t2 = time.perf_counter()

    capture_ms = (t1 - t0) * 1000
    metadata_ms = (t2 - t1) * 1000

    capture_sum += capture_ms
    metadata_sum += metadata_ms

    print(
        f"{i+1:5d} | "
        f"{capture_ms:11.2f} | "
        f"{metadata_ms:12.2f} | "
        f"{metadata['SensorTimestamp']}"
    )

print("\n===== Average =====")
print(f"Capture : {capture_sum / FRAME_COUNT:.2f} ms")
print(f"Metadata: {metadata_sum / FRAME_COUNT:.2f} ms")