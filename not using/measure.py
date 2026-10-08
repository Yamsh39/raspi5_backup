import pandas as pd
import numpy as np

# 1. データの読み込み
# power_log.csv: [timestamp, voltage, current] の形式を想定
# detection_time.log: [status, timestamp] の形式を想定
df_power = pd.read_csv('power_log.csv')
df_exec = pd.read_csv('detection_time.log', header=None, names=['status', 'timestamp'])

# タイムスタンプを数値型に変換
df_power['timestamp'] = pd.to_numeric(df_power['timestamp'])
start_t = float(df_exec[df_exec['status'] == 'start']['timestamp'].values[0])
end_t = float(df_exec[df_exec['status'] == 'end']['timestamp'].values[0])

# 2. 物体検出実行中のデータのみを抽出
mask = (df_power['timestamp'] >= start_t) & (df_power['timestamp'] <= end_t)
df_active = df_power.loc[mask].copy()

# 3. 消費電力(W)の計算
df_active['watt'] = df_active['voltage'] * df_active['current']

# 4. 総エネルギー(Ws)の計算（台形積分）
# 時間軸(x)と電力(y)を使って面積を求める
energy_ws = np.trapz(df_active['watt'], x=df_active['timestamp'])

# 5. 平均電力(W)の計算
duration = end_t - start_t
average_watt = energy_ws / duration

print(f"--- 解析結果 ---")
print(f"処理時間: {duration:.2f} 秒")
print(f"平均消費電力: {average_watt:.3f} W")
print(f"総消費エネルギー: {energy_ws:.3f} Ws")

# 資料のように「1フレームあたり」を出したい場合 (例: 300枚処理したなら)
# print(f"1フレームあたりのエネルギー: {energy_ws / 300:.3f} Ws/frame")
