#!/usr/bin/env python3
"""
Raspberry Pi 5 の内蔵RTCでアラームをセットしてシャットダウンするスクリプト。

前提: rpi-eeprom-config で POWER_OFF_ON_HALT=1 / WAKE_ON_GPIO=0 を設定済み
実行: sudo python3 rtc_wake.py --after 600
      sudo python3 rtc_wake.py --at "2026-10-16 07:00"
"""

import argparse
import subprocess
import sys
import time
from datetime import datetime

WAKEALARM = "/sys/class/rtc/rtc0/wakealarm"


def clear_alarm():
    """既存のアラームを解除する（セット済みだと上書きできないため）"""
    with open(WAKEALARM, "w") as f:
        f.write("0")


def set_alarm_epoch(epoch: int):
    """UNIX時刻でアラームをセットする"""
    clear_alarm()
    with open(WAKEALARM, "w") as f:
        f.write(str(epoch))


def set_wake_after(seconds: int):
    """今から seconds 秒後に起動"""
    set_alarm_epoch(int(time.time()) + seconds)


def set_wake_at(dt: datetime):
    """指定日時に起動（ローカル時刻として解釈）"""
    epoch = int(dt.timestamp())
    if epoch <= time.time():
        raise ValueError("過去の時刻は指定できません")
    set_alarm_epoch(epoch)


def get_alarm():
    """セット中のアラームを datetime で返す（未設定なら None）"""
    with open(WAKEALARM) as f:
        value = f.read().strip()
    return datetime.fromtimestamp(int(value)) if value else None


def shutdown():
    subprocess.run(["shutdown", "-h", "now"], check=True)


def main():
    p = argparse.ArgumentParser(description="Pi 5 RTC wake + shutdown")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--after", type=int, help="N秒後に起動")
    g.add_argument("--at", help='起動日時 例: "2026-10-16 07:00"')
    g.add_argument("--clear", action="store_true", help="アラーム解除のみ")
    p.add_argument("--no-shutdown", action="store_true",
                   help="アラームだけセットしてシャットダウンしない")
    args = p.parse_args()

    try:
        if args.clear:
            clear_alarm()
            print("アラームを解除しました")
            return
        if args.after is not None:
            set_wake_after(args.after)
        else:
            set_wake_at(datetime.strptime(args.at, "%Y-%m-%d %H:%M"))
    except PermissionError:
        sys.exit("権限がありません。sudo で実行してください")

    print(f"起動予定: {get_alarm():%Y-%m-%d %H:%M:%S}")

    if not args.no_shutdown:
        print("シャットダウンします")
        shutdown()


if __name__ == "__main__":
    main()