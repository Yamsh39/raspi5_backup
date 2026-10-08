import requests
import time

TEST_COUNT = 1000
IMAGE_PATH = "/home/pi/Documents/try1000/image.jpg"

with open(IMAGE_PATH, "rb") as f:
    jpg = f.read()

url = "http://192.168.3.13:3000/upload"

start = time.perf_counter()

for i in range(TEST_COUNT):

    response = requests.post(
        url,
        data=jpg,
        headers={
            "Content-Type": "image/jpeg"
        }
    )

end = time.perf_counter()

avg_ms = (end - start) * 1000 / TEST_COUNT

print(f"Average WiFi Send Time = {avg_ms:.3f} ms")