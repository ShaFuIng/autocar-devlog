"""最終版 run-b541：控制端讀到的 IMU 資料年齡（imu_age_s）分布，用來佐證紀錄程式的實際更新頻率。
用法：python -I tools/stats_imu_age.py"""
import json
RUN = 'D:/OneDrive/Desktop/自走車/Orin_Interface_v1/laptop_workbench/data/experiments/run-b541-20261123/pid.jsonl'
ages = []
for line in open(RUN, encoding='utf-8'):
    try: r = json.loads(line)
    except ValueError: continue
    if r.get('kind') != 'sample': continue
    for src in (r['proposal'].get('heading_hold') or {}, r['proposal'].get('imu_boost') or {}, r['vision'].get('dash_route') or {}):
        if isinstance(src, dict) and src.get('imu_age_s') is not None: ages.append(src['imu_age_s']); break
ages.sort(); n = len(ages)
print('n', n, 'min', ages[0], 'p50', ages[n // 2], 'p95', ages[int(n * .95)], 'max', ages[-1])
