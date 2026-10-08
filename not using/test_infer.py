from hailo_platform import (
    HEF,
    VDevice,
    InferVStreams,
    ConfigureParams,
    HailoStreamInterface,
    InputVStreamParams,
    OutputVStreamParams
)
import numpy as np
import cv2

hef_path = "/usr/share/hailo-models/yolov8s_h8.hef"

hef = HEF(hef_path)
target = VDevice()

configure_params = ConfigureParams.create_from_hef(
    hef,
    interface=HailoStreamInterface.PCIe
)

network_group = target.configure(hef, configure_params)[0]

input_vstreams_params = InputVStreamParams.make_from_network_group(network_group)
output_vstreams_params = OutputVStreamParams.make_from_network_group(network_group)

img = cv2.imread("test.jpg")
img = cv2.resize(img, (640, 640))
img = np.expand_dims(img.astype(np.uint8), axis=0)

with InferVStreams(network_group, input_vstreams_params, output_vstreams_params) as infer_pipeline:
    with network_group.activate():
        results = infer_pipeline.infer({"yolov8s/input_layer1": img})

print(results)
