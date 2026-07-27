from hailo_platform import (
    HEF, VDevice, InferVStreams, ConfigureParams,
    HailoStreamInterface, InputVStreamParams, OutputVStreamParams
)
import numpy as np
import cv2

hef_path = "/usr/share/hailo-models/yolov8s_h8.hef"

hef = HEF(hef_path)
target = VDevice()

configure_params = ConfigureParams.create_from_hef(
    hef, interface=HailoStreamInterface.PCIe
)

CLASS_NAMES = [
    "person", "bicycle", "car", "motorcycle", "airplane",
    "bus", "train", "truck", "boat"
]

network_group = target.configure(hef, configure_params)[0]

input_vstreams_params = InputVStreamParams.make_from_network_group(network_group)
output_vstreams_params = OutputVStreamParams.make_from_network_group(network_group)

img = cv2.imread("test.jpg")
orig = img.copy()
h, w = orig.shape[:2]

img_resized = cv2.resize(img, (640, 640))
img_resized = np.expand_dims(img_resized.astype(np.uint8), axis=0)

with InferVStreams(network_group, input_vstreams_params, output_vstreams_params) as infer_pipeline:
    with network_group.activate():
        results = infer_pipeline.infer({"yolov8s/input_layer1": img_resized})

detections = results["yolov8s/yolov8_nms_postprocess"][0]

for class_id, boxes in enumerate(detections):
    for box in boxes:
        y1, x1, y2, x2, conf = box
        if conf < 0.5:
            continue

        x1 = int(x1 * w)
        x2 = int(x2 * w)
        y1 = int(y1 * h)
        y2 = int(y2 * h)

        cv2.rectangle(orig, (x1, y1), (x2, y2), (0,255,0), 2)
        cv2.putText(orig, f"{CLASS_NAMES[class_id]}:{conf:.2f}",
                    (x1, y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0,255,0),
                    2)

cv2.imwrite("result.jpg", orig)
print("saved result.jpg")
