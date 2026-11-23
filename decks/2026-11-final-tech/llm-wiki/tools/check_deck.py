"""節點 G（靜態部分）：python tools/check_deck.py <deck index.html>
檢查：頁數 15、每頁 data-wiki 條目存在、圖片存在、相對路徑、不公開資訊、無 <style>/<script>（除共用檔）、
每頁數字是否出現在該頁連到的 Wiki 條目（找不到列為待人工核對）、舊簡報 git 無變更。輸出 checks/deck-<時間>.md。"""
import re, sys, html, subprocess, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / 'wiki'
PRIV = [r'\b(?:\d{1,3}\.){3}\d{1,3}\b', r'[\w.+-]+@[\w-]+\.[\w.]+', r'\.ssh|_ed25519', r'PRIVATE_HOST_OR_WIFI_NAMES']


def main():
    deck = Path(sys.argv[1]); text = deck.read_text(encoding='utf-8'); d = deck.parent
    issues, notes = [], []
    slides = re.findall(r'<section class="slide[^"]*"(.*?)>(.*?)</section>', text, re.S)
    if len(slides) != 15: issues.append(('全份', 'render', '頁數 %d，應為 15' % len(slides)))
    if re.search(r'<style|<script(?![^>]*src=)', text): issues.append(('全份', 'render', '簡報內有 <style> 或內嵌 <script>（規則禁止）'))
    for i, (attrs, body) in enumerate(slides, 1):
        m = re.search(r'data-wiki="([^"]*)"', attrs)
        ids = [x.strip() for x in (m.group(1).split(',') if m else []) if x.strip()]
        if not ids: issues.append(('P%02d' % i, 'coverage-gap-outline', '沒有 data-wiki'))
        corpus = ''
        for x in ids:
            f = WIKI / (x + '.md')
            if not f.exists(): issues.append(('P%02d' % i, 'link-broken', 'data-wiki 條目不存在：%s' % x))
            else: corpus += f.read_text(encoding='utf-8')
        for src in re.findall(r'(?:src|href|poster)="([^"#]+)"', body):
            if src.startswith(('http:', 'https:', '/')): issues.append(('P%02d' % i, 'render', '非相對路徑：%s' % src)); continue
            if not (d / src).exists(): issues.append(('P%02d' % i, 'render', '檔案不存在：%s' % src))
        vis = html.unescape(re.sub(r'<aside class="teacher-note">.*?</aside>', ' ', body, flags=re.S))
        vis = re.sub(r'<[^>]+>', ' ', vis)
        nums = sorted(set(n for n in re.findall(r'\d+(?:\.\d+)?', vis) if len(n.replace('.', '')) >= 2))
        miss = [n for n in nums if n not in corpus]
        if miss: notes.append(('P%02d' % i, '數字未在 data-wiki 條目出現（待人工／AI 核對）：%s' % ', '.join(miss[:20])))
    for rx in PRIV:
        for m in re.finditer(rx, text):
            if re.fullmatch(r'\d+\.\d+\.\d+', m.group(0)): continue
            issues.append(('全份', 'privacy', m.group(0)))
    repo = d.parents[1]
    r = subprocess.run(['git', '-C', str(repo), 'status', '--porcelain', '--', 'decks/2026-11-dev-overview'], capture_output=True, text=True)
    if r.stdout.strip(): issues.append(('舊簡報', 'render', '舊簡報有變更：%s' % r.stdout.strip()))
    ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    out = ['# 簡報靜態檢查 %s' % ts, '', '- 檔案：%s' % deck, '- 頁數 %d；問題 %d；待核對 %d' % (len(slides), len(issues), len(notes)), '', '## 問題', '']
    out += ['- [%s] %s：%s' % (t, p, m) for p, t, m in issues] or ['- 無']
    out += ['', '## 待核對（數字追溯）', ''] + (['- %s：%s' % n for n in notes] or ['- 無'])
    (ROOT / 'checks' / ('deck-%s.md' % ts)).write_text('\n'.join(out) + '\n', encoding='utf-8')
    print('slides %d issues %d notes %d -> deck-%s.md' % (len(slides), len(issues), len(notes), ts))
    sys.exit(1 if issues else 0)


if __name__ == '__main__':
    main()
