#!/usr/bin/env python3
"""
Pi側のJPEG出力を確認するスクリプト
- 修正版（RGB888, queue=False）と旧設定（デフォルトXBGR8888）で1枚ずつ保存
- 解像度・バイト数・推定JPEG品質を表示
- 2枚を横に並べた比較画像も保存（色の入れ替わり確認用）
"""
import os
import time

import cv2
from PIL import Image
from picamera2 import Picamera2

SIZE = (640, 480)
QUALITY = 80
WARMUP = 10
OUT_DIR = "jpeg_check"


def estimate_quality(path):
    """量子化テーブル（輝度DC）からlibjpeg相当の品質を概算"""
    dc = Image.open(path).quantization[0][0]
    s = dc * 100 / 16
    q = (5000 / s) if s > 100 else (200 - s) / 2
    return dc, round(q)


def capture_and_save(picam2, label, fmt, queue):
    if picam2.started:
        picam2.stop()

    config = picam2.create_preview_configuration(
        main={"size": SIZE, "format": fmt},
        queue=queue,
    )
    picam2.configure(config)
    cam_cfg = picam2.camera_configuration()
    picam2.start()

    # ウォームアップ（AE/AWBの安定化）
    for _ in range(WARMUP):
        frame = picam2.capture_array()
        cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, QUALITY])

    t0 = time.perf_counter()
    frame = picam2.capture_array()
    t1 = time.perf_counter()
    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, QUALITY])
    t2 = time.perf_counter()
    if not ok:
        raise RuntimeError("JPEGエンコード失敗")

    path = os.path.join(OUT_DIR, f"{label}.jpg")
    with open(path, "wb") as f:
        f.write(buf.tobytes())

    dc, est_q = estimate_quality(path)
    print(f"--- {label} ---")
    print(f"  main設定      : {cam_cfg['main']['size']} {cam_cfg['main']['format']}")
    print(f"  sensor設定    : {cam_cfg.get('sensor')}")
    print(f"  配列shape     : {frame.shape}  ({frame.nbytes} bytes)")
    print(f"  JPEG          : {Image.open(path).size}  {os.path.getsize(path)} bytes")
    print(f"  輝度DC/推定品質: {dc} / ≈{est_q}")
    print(f"  C {(t1 - t0) * 1000:.2f} ms, J {(t2 - t1) * 1000:.2f} ms（1回のみ・参考値）")
    print(f"  保存先        : {path}")
    return path


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    picam2 = Picamera2()
    try:
        new_path = capture_and_save(picam2, "new_RGB888", "RGB888", queue=False)
        old_path = capture_and_save(picam2, "old_XBGR8888", "XBGR8888", queue=True)
    finally:
        picam2.stop()
        picam2.close()

    # 左：修正版、右：旧設定
    left = cv2.imread(new_path)
    right = cv2.imread(old_path)
    cv2.putText(left, "new RGB888", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(right, "old XBGR8888", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cmp_path = os.path.join(OUT_DIR, "compare.jpg")
    cv2.imwrite(cmp_path, cv2.hconcat([left, right]))
    print(f"\n比較画像: {cmp_path}（左=修正版 / 右=旧設定）")


if __name__ == "__main__":
    main()