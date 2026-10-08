from picamera2 import Picamera2
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

end = time.perf_counter()

avg_ms = (end - start) * 1000 / TEST_COUNT

print(f"Average Capture Time = {avg_ms:.3f} ms")