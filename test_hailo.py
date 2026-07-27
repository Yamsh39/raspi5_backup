from hailo_platform import HEF, VDevice
import numpy as np

hef_path = "/usr/share/hailo-models/yolov8s_h8.hef"

hef = HEF(hef_path)
target = VDevice()

network_group = target.configure(hef)[0]

input_infos = hef.get_input_vstream_infos()
output_infos = hef.get_output_vstream_infos()

print("INPUT:", input_infos)
print("OUTPUT:", output_infos)
