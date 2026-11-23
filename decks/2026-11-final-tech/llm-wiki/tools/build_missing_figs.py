"""補簡報缺圖（P02 曝光對照、P11 一格命令實例、P14 圈速時間線）。只讀 raw 與 run-b541 逐格紀錄。
用法：Python310\\python.exe -I tools/build_missing_figs.py <簡報資料夾>"""
import json, re, sys
from pathlib import Path
import cv2, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(sys.argv[1])
RUN = Path('D:/OneDrive/Desktop/自走車/Orin_Interface_v1/laptop_workbench/data/experiments/run-b541-20261123/pid.jsonl')
font_manager.fontManager.addfont('C:/Windows/Fonts/msjh.ttc')
plt.rcParams.update({'font.family': 'Microsoft JhengHei', 'axes.unicode_minus': False, 'figure.facecolor': '#0f1b26',
                     'axes.facecolor': '#0f1b26', 'text.color': '#e6eef4', 'axes.labelcolor': '#e6eef4', 'xtick.color': '#b9c8d3',
                     'ytick.color': '#b9c8d3', 'axes.edgecolor': '#3a4b59', 'font.size': 12})


def p02():
    """11-17 隧道口靜態曝光比對：取前兩格（自動、手動 30 ms＋gamma 300），上方背景模糊（場邊人員）。"""
    im = cv2.imread(str(ROOT / 'raw/records/analyses/expo-20261117/expo_tunnel.jpg'))
    im = im[:, :960].copy()                      # 前兩組：自動｜m30 g300
    for x0 in (0, 480):
        top = im[0:110, x0:x0 + 480]
        im[0:110, x0:x0 + 480] = cv2.GaussianBlur(top, (0, 0), 9)   # 隱私：背景（含人員）模糊
        cv2.rectangle(im, (x0, 0), (x0 + 480, 30), (15, 27, 38), -1)  # 蓋掉原英文標籤，改由圖說說明
    ok, buf = cv2.imencode('.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 88]); assert ok   # cv2.imwrite 不支援中文路徑
    (OUT / 'p02-exposure-tunnel.jpg').write_bytes(buf.tobytes())


def frames():
    want = {41414: None, 40559: None}
    for l in open(RUN, encoding='utf-8'):
        try: r = json.loads(l)
        except ValueError: continue
        if r.get('kind') == 'sample' and r.get('pid_input_seq') in want:
            want[r['pid_input_seq']] = r['proposal']
        if all(want.values()): break
    return want


def p11():
    f = frames(); c = 1445.0
    st, cv = f[41414], f[40559]
    def pid(p, gain):
        return c + (p['p'] + p['i'] + p['d']) * gain
    # 直線格：PID → 增益縮放 → 陀螺儀內迴圈 → 間隙補償
    g = st['gain_schedule']; yi = st['yaw_inner']; pc = st['play_comp']
    s1 = [('中心', c), ('PID\n(P+I+D)×1.45', st['desired_us']), ('高油門縮放\n×%.2f' % g['k'], c + yi['u_us']),
          ('陀螺儀內迴圈\n%+.0f µs' % yi['term_us'], pc['raw_us']), ('間隙補償\n%+.0f µs' % pc['offset_us'], pc['steer_us'])]
    lf = cv['lap_ff']; pc2 = cv['play_comp']
    s2 = [('中心', c), ('PID\n(P+I+D)', cv['desired_us']), ('前段各層後', lf['pid_steer_us']),
          ('帶狀前饋全權\n(已轉 %.0f°)' % lf['band']['turned_deg'], lf['steer_us']), ('間隙補償\n%+.0f µs' % pc2['offset_us'], pc2['steer_us'])]
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.6))
    for ax, steps, title in [(axs[0], s1, '主直線一格（seq 41414，誤差 %.3f）' % st['error']),
                             (axs[1], s2, '彎 2 一格（seq 40559，誤差 %.3f）' % cv['error'])]:
        xs = range(len(steps)); ys = [v for _, v in steps]
        ax.plot(xs, ys, '-o', color='#57c7a4', lw=2)
        for x, (lab, v) in zip(xs, steps):
            ax.annotate('%.1f' % v, (x, v), textcoords='offset points', xytext=(0, 9), ha='center', fontsize=11, color='#ffd479')
        ax.axhline(c, color='#5b6b78', ls='--', lw=1)
        ax.set_xticks(list(xs)); ax.set_xticklabels([l for l, _ in steps], fontsize=10)
        ax.set_ylabel('舵量 µs（>1445 往右）'); ax.set_title(title, fontsize=13)
        lo, hi = min(ys), max(ys); ax.set_ylim(lo - 0.15 * (hi - lo) - 5, hi + 0.25 * (hi - lo) + 5)
    fig.tight_layout(); fig.savefig(OUT / 'p11-command-chain.png', dpi=100); plt.close(fig)


def p14():
    rows = []
    for line in (ROOT / 'wiki/experiments/lap-progression.md').read_text(encoding='utf-8').splitlines():
        m = re.match(r'^\| (11-\d\d)[^|]*\| (\w{4}) \| ([^|]+)\|', line)
        if not m: continue
        nums = [float(x) for x in re.findall(r'\d+\.\d+', m.group(3))]
        if nums: rows.append((m.group(1), m.group(2), min(nums), '彎 1 計圈' in m.group(3)))
    fig, ax = plt.subplots(figsize=(12, 4.4))
    xs = list(range(len(rows)))
    ax.plot(xs, [r[2] for r in rows], color='#3a6f8f', lw=1.5, zorder=1)
    for x, (d, rid, v, c1) in zip(xs, rows):
        col = '#9aa7b1' if rid in ('6430', '676e') else ('#ffd479' if rid == 'b541' else ('#e07a5f' if rid == '9729' else '#57c7a4'))
        ax.scatter([x], [v], s=90 if rid == 'b541' else 40, facecolors='none' if c1 else col, edgecolors=col, linewidths=2, zorder=2)
    for rid, txt, dy in [('7fbf', '109.9 s', 8), ('b541', '最終版 56.5 s\n（賽前實測）', 18), ('9729', '55.4 s（舊舵機）', -34)]:
        i = [r[1] for r in rows].index(rid); ax.annotate(txt, (i, rows[i][2]), textcoords='offset points', xytext=(-40 if rid == '9729' else 0, dy), ha='center', fontsize=11, color='#ffd479')
    ax.set_xticks(xs); ax.set_xticklabels(['%s\n%s' % (r[0], r[1]) for r in rows], fontsize=8)
    ax.set_ylabel('單圈 s（區間取最快值）')
    ax.set_title('有紀錄的單圈（每點＝當天那一輪；空心＝彎 1 計圈，灰＝相機姿態不可靠）', fontsize=12)
    fig.tight_layout(); fig.savefig(OUT / 'p14-lap-timeline.png', dpi=100); plt.close(fig)


if __name__ == '__main__':
    p02(); p11(); p14(); print('ok')
