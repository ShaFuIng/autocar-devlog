"""stats_timing.py: 最終版實跑 run-b541 的時序統計（只讀）。

用法：python -I tools/stats_timing.py [pid.jsonl 路徑]
預設讀 MANIFEST 中 external 項（run-b541-20261123/pid.jsonl，55 MB，不複製進 raw/）。
只計 kind=='sample' 的列；每列是一次送出的命令（有效格或遺失格）。
- 「新影格」＝vision.seq 與上一列不同的列（遺失格／保持格可能重複帶同一個 vision）。
- inference_ms、stage_ms.*、control_age_s 只在新影格上統計，避免重複計數。
- control_age_s＝consumed_at−capture_at（同一台 Orin 的 monotonic 時鐘），即「相機擷取→PID 消費」的控制資料年齡。
輸出中位數、P95、最小、最大與筆數；每秒命令數與每秒新影格數以 wall 時間跨度計。
"""
import json
import sys

DEFAULT = r'D:\OneDrive\Desktop\自走車\Orin_Interface_v1\laptop_workbench\data\experiments\run-b541-20261123\pid.jsonl'


def pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    k = (len(xs) - 1) * q
    lo = int(k)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def summ(name, xs, scale=1.0, unit=''):
    xs = [x * scale for x in xs if isinstance(x, (int, float))]
    if not xs:
        print(f'{name}: 無資料')
        return
    print(f'{name}: n={len(xs)} 中位數={pct(xs, .5):.1f}{unit} P95={pct(xs, .95):.1f}{unit} '
          f'最小={min(xs):.1f}{unit} 最大={max(xs):.1f}{unit}')


def main(path):
    walls = []
    new_walls = []
    inf, model, path_ms, decode, queue_ms, age = [], [], [], [], [], []
    prev_seq = None
    fseq = []   # (相機 frame_seq, capture_at)：估相機擷取速率與被跳過的影格
    n_sample = 0
    n_valid_flag = 0
    with open(path, encoding='utf-8') as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get('kind') != 'sample':
                continue
            n_sample += 1
            w = d.get('wall')
            if isinstance(w, (int, float)):
                walls.append(w)
            v = d.get('vision') or {}
            seq = v.get('seq')
            if seq is None or seq == prev_seq:
                continue
            prev_seq = seq
            if isinstance(w, (int, float)):
                new_walls.append(w)
            if v.get('valid') is True:
                n_valid_flag += 1
            inf.append(v.get('inference_ms'))
            st = v.get('stage_ms') or {}
            model.append(st.get('model'))
            path_ms.append(st.get('path'))
            decode.append(st.get('decode'))
            queue_ms.append(st.get('queue'))
            fs = v.get('frame_seq')
            if isinstance(fs, int) and isinstance(v.get('capture_at'), (int, float)):
                fseq.append((fs, v['capture_at']))
            ca, co = v.get('capture_at'), v.get('consumed_at')
            if isinstance(ca, (int, float)) and isinstance(co, (int, float)):
                age.append(co - ca)
            elif isinstance(v.get('control_age_s'), (int, float)):
                age.append(v['control_age_s'])
    span = (max(walls) - min(walls)) if len(walls) > 1 else None
    print(f'檔案：{path}')
    print(f'sample 列數={n_sample}，新影格數={len(new_walls)}（其中 vision.valid=True {n_valid_flag}）')
    if span:
        print(f'wall 跨度={span:.1f} s；每秒命令（sample 列）={n_sample / span:.2f}；每秒新影格={len(new_walls) / span:.2f}')
    if len(new_walls) > 1:
        gaps = [b - a for a, b in zip(new_walls, new_walls[1:])]
        summ('新影格間隔（PID 消費端，wall）', gaps, 1000., ' ms')
    if len(fseq) > 1:
        (f0, c0), (f1, c1) = fseq[0], fseq[-1]
        if c1 > c0:
            print(f'相機 frame_seq 跨度={f1 - f0}，capture_at 跨度={c1 - c0:.1f} s → 相機擷取約 {(f1 - f0) / (c1 - c0):.2f} 張/s；'
                  f'被 PID 消費的比例約 {len(fseq) / (f1 - f0 + 1):.2f}')
    summ('vision.inference_ms', inf, 1., ' ms')
    summ('stage_ms.model', model, 1., ' ms')
    summ('stage_ms.path', path_ms, 1., ' ms')
    summ('stage_ms.decode', decode, 1., ' ms')
    summ('stage_ms.queue', queue_ms, 1., ' ms')
    summ('控制資料年齡 consumed_at−capture_at', age, 1000., ' ms')


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT)
