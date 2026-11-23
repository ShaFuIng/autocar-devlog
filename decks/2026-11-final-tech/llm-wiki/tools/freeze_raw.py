"""節點 A：把自走車最終版的原始資料凍結複製到 raw/，並產生 raw/MANIFEST.tsv。

只讀來源（自走車專案），只寫本 Wiki 的 raw/。已存在的 raw 檔若雜湊不同就停下（不覆寫）。
用法：python tools/freeze_raw.py
"""
import csv, hashlib, shutil, sys, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'raw'
P = Path('D:/OneDrive/Desktop/自走車')
EXP = P / 'Orin_Interface_v1/laptop_workbench/data/experiments'
SNAP = EXP / 'orin-web-snapshot-20261123d'

# (來源, raw 內目的地, 類別, 說明)
ITEMS = []
def add(src, dst, kind, note):
    ITEMS.append((Path(src), dst, kind, note))

# 1. 最終版車上程式＋設定（整個快照，201＋2 檔）
for f in sorted(SNAP.rglob('*')):
    if f.is_file():
        add(f, 'project/snapshot-20261123d/' + f.relative_to(SNAP).as_posix(), 'final-code',
            '最終版車上 web/ 快照（使用者定版 11-23）')
# 2. 現役韌體原始碼（pwm100_v1）
FW = P / 'firmware_builds/pwm100_v1'
for f in sorted((FW / 'Orin_Interface_v1').glob('*')):
    if f.is_file():
        add(f, 'project/firmware-pwm100_v1/' + f.name, 'final-firmware', '現役韌體原始碼（11-19 起）')
add(FW / 'acceptance.json', 'project/firmware-pwm100_v1/acceptance.json', 'final-firmware', '燒錄驗收紀錄')
# 3. 協定與硬體說明
add(P / 'Orin_Interface_v1/PROTOCOL.md', 'project/docs/PROTOCOL.md', 'project-doc', 'Orin–BMduino UART 協定')
add(P / 'Orin_Interface_v1/README.md', 'project/docs/Orin_Interface_v1-README.md', 'project-doc', '控制板韌體說明（含硬體）')
add(P / '車2_UART通訊協定與Checksum說明.pdf', 'project/docs/team-uart-protocol.pdf', 'project-doc', '團隊自撰 UART 協定說明（非獨立來源）')
add(P / 'jetson_orin_nano_environment_handoff.md', 'project/docs/jetson-environment-handoff.md', 'project-doc', 'Orin 環境紀錄（JetPack 版本等）')
add(P / '跑道地圖_統一版_01-12.webp', 'project/docs/track-map-01-12.webp', 'project-doc', '統一跑道地圖（使用者指定）')
# 4. IMU 紀錄程式（11-05 版；現役版本未逐檔確認）
add(EXP / 'imu-new-20261105/imu_logger.py', 'project/imu-new-20261105/imu_logger.py', 'project-code', 'IMU 紀錄程式 11-05 版（現役是否相同未證實）')
add(EXP / 'imu-new-20261105/acceptance.json', 'project/imu-new-20261105/acceptance.json', 'project-code', 'IMU 新晶片驗收')
# 5. 模型
Y = P / 'yolo26_sem_v4_trial'
for rel in ['runs/trial01/args.yaml', 'dataset/data.yaml', 'comparison/metrics.json', 'training_summary.json',
            'train_trial.py', 'run_provenance.json', 'split_plan.json', 'quality_gate.json']:
    if (Y / rel).exists():
        add(Y / rel, 'project/model-yolo26-sem-v4/' + rel, 'model', 'YOLO26 語意分割 v4（部署權重來源）')
# 6. 分析與實驗紀錄
add(EXP / 'why-s-weave-20261107/findings.json', 'records/analyses/why-s-weave-20261107-findings.json', 'analysis', '直線 S 型原因分析')
add(EXP / 'play-comp-20261105/findings.json', 'records/analyses/play-comp-20261105-findings.json', 'analysis', '轉向間隙補償分析')
add(P / 'Orin_Interface_v1/laptop_workbench/data/tracking-proposal-v1.json', 'records/analyses/tracking-proposal-v1.json', 'analysis', '循跡控制器提案（Pure Pursuit 等）')
add(P / 'AI_自走車_A1海報_Claude查核回覆_v1.md', 'records/analyses/a1-poster-factcheck-20261103.md', 'analysis', '11-03 查核回覆（部分數字已過時）')
# 7. 開發紀錄（原檔完整複本）
add(P / 'AGENTS.md', 'records/logs/AGENTS.md', 'log', '專案規則與車上現況（11-23 19:40 版）')
add(P / 'AGENTS_LOG_202611.md', 'records/logs/AGENTS_LOG_202611.md', 'log', '11-19 以後逐日紀錄')
add(P / 'AGENTS_HISTORY_until_20261119.md', 'records/logs/AGENTS_HISTORY_until_20261119.md', 'log', '11-19 以前完整紀錄')
# 8. 最終版實跑
add(EXP / 'run-b541-20261123/summary.json', 'records/runs/run-b541-20261123/summary.json', 'run', '最終版實跑 run-b541 摘要')
# 9. 官方文件（專案內已有）
add(P / 'Jetson-Orin-Nano-DevKit-Carrier-Board-Specification_SP-11324-001_v1.3.pdf',
    'official/nvidia-jetson-orin-nano-carrier-board-SP-11324-001-v1.3.pdf', 'official', 'NVIDIA 官方載板規格書')

# 只記錄、不複製的大檔（以原路徑＋雜湊追溯）
EXTERNAL = [(EXP / 'run-b541-20261123/pid.jsonl', 'run', '最終版實跑逐格紀錄（55 MB，不複製）')]


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def main():
    # 快照完整性：與快照自己的 MANIFEST.sha256 比對
    bad = []
    for line in (SNAP / 'MANIFEST.sha256').read_text(encoding='utf-8').splitlines():
        parts = line.split()
        if len(parts) >= 2:
            h, name = parts[0], parts[-1].lstrip('*')
            f = SNAP / name
            if f.exists() and sha(f) != h: bad.append(name)
    if bad:
        sys.exit('快照與其 MANIFEST 不符：%s' % bad)
    rows = []
    today = datetime.date.today().isoformat()
    for src, dst, kind, note in ITEMS:
        if not src.exists(): sys.exit('來源不存在：%s' % src)
        h = sha(src); out = RAW / dst
        if out.exists():
            if sha(out) != h: sys.exit('raw 已存在但內容不同，停止：%s' % dst)
        else:
            out.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, out)
            if sha(out) != h: sys.exit('複製後雜湊不符：%s' % dst)
        rows.append(['raw/' + dst, str(src), h, src.stat().st_size, kind, 'copied', today, note])
    for src, kind, note in EXTERNAL:
        rows.append(['', str(src), sha(src), src.stat().st_size, kind, 'external', today, note])
    with open(RAW / 'MANIFEST.tsv', 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter='\t')
        w.writerow(['raw_path', 'source_path', 'sha256', 'bytes', 'kind', 'mode', 'frozen_on', 'note'])
        w.writerows(rows)
    print('ok', len(rows), 'entries; snapshot manifest verified')


if __name__ == '__main__':
    main()
