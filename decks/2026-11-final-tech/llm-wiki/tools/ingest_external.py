"""節點 B：把已下載的外部文獻放進 raw/，附文字抽取檔，追加 raw/MANIFEST.tsv。
用法：python tools/ingest_external.py <下載資料夾>
文字抽取檔（*.txt）是由原檔機械轉出的衍生檔，供行號引用；原檔與抽取檔都記入 MANIFEST。"""
import csv, hashlib, html, re, shutil, sys, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'raw'
TODAY = datetime.date.today().isoformat()
# (下載檔名, raw 目的地, 來源網址, 版本說明, 類別)
ITEMS = [
    ('ultralytics-semantic.html', 'official/ultralytics-docs-tasks-semantic.html', 'https://docs.ultralytics.com/tasks/semantic/', 'Ultralytics 線上文件（擷取當日版本）', 'official'),
    ('ultralytics-segment.html', 'official/ultralytics-docs-tasks-segment.html', 'https://docs.ultralytics.com/tasks/segment/', 'Ultralytics 線上文件（擷取當日版本）', 'official'),
    ('ultralytics-jetson.html', 'official/ultralytics-docs-guides-nvidia-jetson.html', 'https://docs.ultralytics.com/guides/nvidia-jetson/', 'Ultralytics 線上文件（擷取當日版本）', 'official'),
    ('opencv-homography.html', 'official/opencv-4.13.0-tutorial-homography.html', 'https://docs.opencv.org/4.x/d9/dab/tutorial_homography.html', 'OpenCV 4.13.0 文件（4.x 轉址）', 'official'),
    ('mpu-ds2.pdf', 'official/invensense-RM-MPU-6000A-register-map.pdf', 'https://cdn.sparkfun.com/datasheets/Sensors/Accelerometers/RM-MPU-6000A.pdf', 'InvenSense RM-MPU-6000A（MPU-6000/6050 暫存器表）；官方網址轉到搜尋頁，改取經銷商鏡像', 'official'),
    ('rpp-2305.20026.pdf', 'papers/macenski-2023-regulated-pure-pursuit-arxiv-2305.20026.pdf', 'https://arxiv.org/pdf/2305.20026', 'arXiv 2305.20026（擷取當日最新版）', 'paper'),
    ('rpp-2305.20026-abs.html', 'papers/macenski-2023-regulated-pure-pursuit-arxiv-2305.20026-abs.html', 'https://arxiv.org/abs/2305.20026', 'arXiv 摘要頁', 'paper'),
    ('stanley05.pdf', 'papers/thrun-2006-stanley.pdf', 'http://robots.stanford.edu/papers/thrun.stanley05.pdf', 'Stanford 作者頁 PDF', 'paper'),
]


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def html_text(s):
    s = re.sub(r'(?is)<(script|style|svg|noscript)\b.*?</\1>', ' ', s)
    s = re.sub(r'(?i)<br\s*/?>|</(p|div|h[1-6]|li|tr|pre|table|section|code)>', '\n', s)
    s = html.unescape(re.sub(r'<[^>]+>', ' ', s))
    lines = [re.sub(r'[ \t ]+', ' ', l).strip() for l in s.splitlines()]
    return '\n'.join(l for l in lines if l) + '\n'


def main():
    dl = Path(sys.argv[1])
    rows = []
    for name, dst, url, ver, kind in ITEMS:
        src = dl / name
        data = src.read_bytes()
        if dst.endswith('.pdf') and not data.startswith(b'%PDF'): sys.exit('不是 PDF：%s' % name)
        if dst.endswith('.html') and b'<html' not in data[:5000].lower() and b'<!doctype' not in data[:200].lower(): sys.exit('不是 HTML：%s' % name)
        out = RAW / dst
        if out.exists() and sha(out) != sha(src): sys.exit('raw 已存在且不同：%s' % dst)
        out.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, out)
        rows.append(['raw/' + dst, url, sha(out), out.stat().st_size, kind, 'downloaded', TODAY, ver])
        if dst.endswith('.html'):
            txt = out.with_suffix('.txt')
            txt.write_text(html_text(data.decode('utf-8', 'replace')), encoding='utf-8')
            rows.append(['raw/' + dst[:-5] + '.txt', 'derived from raw/' + dst, sha(txt), txt.stat().st_size, kind, 'derived-text', TODAY, '由 tools/ingest_external.py 去標籤轉出，供行號引用'])
    with open(RAW / 'MANIFEST.tsv', 'a', encoding='utf-8', newline='') as f:
        csv.writer(f, delimiter='\t').writerows(rows)
    for r in rows: print(r[0], r[3], r[2][:12])


if __name__ == '__main__':
    main()
