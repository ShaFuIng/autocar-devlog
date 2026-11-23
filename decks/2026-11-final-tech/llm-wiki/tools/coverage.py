"""節點 E：大綱覆蓋率與來源檢查。python tools/coverage.py [deck/outline.md]
輸出 checks/coverage-<時間>.md；結束碼 0＝通過。"""
import re, sys, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / 'wiki'
LINK = re.compile(r'\[\[([^\]|#]+)\]\]')
NUMRX = re.compile(r'\d+(?:\.\d+)?')
FIELDS = ['結論', '感測／演算法', 'Wiki', '公式', '圖表', '待決']


def status(pid):
    t = (WIKI / (pid + '.md')).read_text(encoding='utf-8')
    m = re.search(r'^status:\s*(\S+)', t, re.M)
    return m.group(1) if m else None


def main():
    outline = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'deck/outline.md'
    text = outline.read_text(encoding='utf-8')
    conflicts = (WIKI / 'conflicts.md').read_text(encoding='utf-8')
    pages = re.split(r'^## (P\d\d) ', text, flags=re.M)[1:]
    pages = list(zip(pages[0::2], pages[1::2]))
    issues, rows = [], []
    if len(pages) != 15: issues.append(('全份', 'coverage-gap-outline', '頁數 %d，應為 15' % len(pages)))
    for pno, body in pages:
        title = body.split('\n', 1)[0].strip()
        f = {}
        for k in FIELDS:
            m = re.search(r'^- %s：(.*)$' % re.escape(k), body, re.M)
            if not m: issues.append((pno, 'coverage-gap-outline', '缺欄位「%s」' % k))
            f[k] = m.group(1) if m else ''
        links = LINK.findall(f['Wiki'])
        missing = [l for l in links if not (WIKI / (l + '.md')).exists()]
        if not links: issues.append((pno, 'coverage-gap-wiki', '沒有連到任何 Wiki 條目'))
        for l in missing: issues.append((pno, 'coverage-gap-wiki', '條目不存在：%s' % l))
        ok_links = [l for l in links if l not in missing]
        sts = {l: status(l) for l in ok_links}
        n = int(pno[1:])
        if n <= 13 and not any(s in ('implemented', 'mixed') for s in sts.values()):
            issues.append((pno, 'coverage-gap-wiki', '技術頁沒有現役（implemented／mixed）條目'))
        corpus = '\n'.join((WIKI / (l + '.md')).read_text(encoding='utf-8') for l in ok_links)
        bad_nums = []
        for num in NUMRX.findall(f['結論']):
            if num not in corpus: bad_nums.append(num)
        for num in bad_nums: issues.append((pno, 'coverage-gap-outline', '結論數字 %s 在連到的條目中找不到' % num))
        for cid in re.findall(r'\b([A-Z]{1,2}-?\d+)\b', f['待決']):
            if not re.search(r'(^|\n)#+ %s\b|\| %s \|' % (re.escape(cid), re.escape(cid)), conflicts):
                issues.append((pno, 'link-broken', '衝突編號不存在：%s' % cid))
        rows.append((pno, title, ', '.join('%s(%s)' % (l, sts.get(l, '缺')) for l in links), len(bad_nums)))
    tech = sum(1 for p, _ in pages if int(p[1:]) <= 13)
    ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    out = ['# 覆蓋率檢查 %s' % ts, '', '- 頁數 %d；技術頁（P01–P13）%d、演進與失敗頁 %d（%.0f%% / %.0f%%）' % (
        len(pages), tech, len(pages) - tech, 100 * tech / max(1, len(pages)), 100 * (len(pages) - tech) / max(1, len(pages))),
        '- 問題 %d' % len(issues), '', '| 頁 | 題目 | 條目(狀態) | 結論數字無出處 |', '|---|---|---|---|']
    out += ['| %s | %s | %s | %d |' % r for r in rows]
    out += ['', '## 問題', ''] + (['- [%s] %s：%s' % (t, p, m) for p, t, m in issues] or ['- 無'])
    (ROOT / 'checks' / ('coverage-%s.md' % ts)).write_text('\n'.join(out) + '\n', encoding='utf-8')
    print('pages %d issues %d -> coverage-%s.md' % (len(pages), len(issues), ts))
    for p, t, m in issues: print(' ', p, t, m)
    sys.exit(1 if issues else 0)


if __name__ == '__main__':
    main()
