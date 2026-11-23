"""節點 C 自動檢查：python tools/lint.py [--log ISSUE_PREFIX]
輸出 checks/lint-<時間>.md 與 checks/lint-latest.json；結束碼 0＝無錯誤、1＝有錯誤。
檢查項目見 AGENTS.md 第 6 節。"""
import csv, hashlib, json, re, sys, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / 'wiki'
STATUS = {'implemented', 'used-before', 'reference-only', 'mixed'}
SECTIONS = ['## 一句話結論', '## 內容', '## 公式與參數', '## 未確認', '## 相關條目']
SPECIAL = {'index', 'log', 'conflicts'}          # 不套用條目格式的頁
SRC = re.compile(r'\[src:\s*(raw/[^\]#\s]+)(?:#([^\]]+))?\]')
LINK = re.compile(r'\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]')
NUM = re.compile(r'\d')
PRIV = [(re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'), 'IP 位址'),
        (re.compile(r'[\w.+-]+@[\w-]+\.[\w.]+'), '電子郵件'),
        (re.compile(r'\.ssh|_ed25519|id_rsa', re.I), '金鑰路徑'),
        (re.compile(r'PRIVATE_HOST_OR_WIFI_NAMES', re.I), '主機或網路名稱')]
PRIV_ALLOW = re.compile(r'\b(?:0x[0-9a-f]+|\d+\.\d+\.\d+)\b')   # 版本號等


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def frontmatter(text):
    if not text.startswith('---'): return None, text
    end = text.find('\n---', 3)
    if end < 0: return None, text
    fm, body = text[3:end], text[end + 4:]
    d = {}; key = None
    for line in fm.splitlines():
        if re.match(r'^\s+-\s+', line) and key:
            d.setdefault(key, []).append(line.split('-', 1)[1].strip())
        elif ':' in line:
            k, v = line.split(':', 1); key = k.strip(); v = v.split('#')[0].strip()
            d[key] = v if v else []
    return d, body


def main():
    errors, warns = [], []
    manifest = {}
    with open(ROOT / 'raw/MANIFEST.tsv', encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if r['raw_path']: manifest[r['raw_path']] = r['sha256']
    shacache, linecache = {}, {}
    pages = {p.relative_to(WIKI).with_suffix('').as_posix(): p for p in WIKI.rglob('*.md')}
    index_text = (WIKI / 'index.md').read_text(encoding='utf-8') if (WIKI / 'index.md').exists() else ''
    linked = set()
    n_cites = 0
    for pid, p in sorted(pages.items()):
        text = p.read_text(encoding='utf-8')
        fm, body = frontmatter(text)
        rel = 'wiki/' + pid + '.md'
        if pid not in SPECIAL:
            if fm is None: errors.append((rel, 'link-broken', '缺 frontmatter')); continue
            if fm.get('id') != pid: errors.append((rel, 'link-broken', 'id 與路徑不符：%s' % fm.get('id')))
            if fm.get('status') not in STATUS: errors.append((rel, 'status-wrong', 'status 無效：%s' % fm.get('status')))
            for s in SECTIONS:
                if s not in body: errors.append((rel, 'uncited', '缺段落 %s' % s))
            for s in fm.get('sources') or []:
                if s not in manifest: errors.append((rel, 'raw-missing', 'sources 不在 MANIFEST：%s' % s))
            if ('[[%s]]' % pid) not in index_text:
                errors.append((rel, 'link-broken', 'index.md 沒列這頁'))
        in_code = False
        for ln, line in enumerate(body.splitlines(), 1):
            if line.strip().startswith('```'): in_code = not in_code; continue
            for m in SRC.finditer(line):
                n_cites += 1
                path, frag = m.group(1), m.group(2)
                if path not in manifest: errors.append((rel, 'raw-missing', '引用不在 MANIFEST：%s' % path)); continue
                f = ROOT / path
                if not f.exists(): errors.append((rel, 'raw-missing', 'raw 檔不存在：%s' % path)); continue
                if path not in shacache: shacache[path] = sha(f)
                if shacache[path] != manifest[path]: errors.append((rel, 'raw-missing', '雜湊不符：%s' % path))
                if frag:
                    if path not in linecache:
                        try: linecache[path] = f.read_text(encoding='utf-8', errors='replace')
                        except Exception: linecache[path] = ''
                    src = linecache[path]
                    mm = re.fullmatch(r'L(\d+)(?:-L?(\d+))?', frag)
                    if mm:
                        a = int(mm.group(1)); b = int(mm.group(2) or a); n = src.count('\n') + 1
                        if not (1 <= a <= b <= n): errors.append((rel, 'link-broken', '行號超出 %s#%s（共 %d 行）' % (path, frag, n)))
                    elif frag.startswith('key='):
                        k = frag[4:]
                        for part in k.split('.'):
                            if ('"%s"' % part) not in src and part not in src:
                                errors.append((rel, 'link-broken', 'json 鍵不存在 %s#%s' % (path, frag))); break
                    else:
                        errors.append((rel, 'link-broken', '錨點格式錯誤 %s#%s' % (path, frag)))
            for m in LINK.finditer(line):
                t = m.group(1).strip(); linked.add(t)
                if t not in pages: errors.append((rel, 'link-broken', '條目連結無效 [[%s]]（第 %d 行）' % (t, ln)))
            if pid not in SPECIAL and not in_code:
                s = line.strip()
                if s and not s.startswith('#') and not s.startswith('|---') and NUM.search(s) and 'src:' not in s and '[[' not in s:
                    if not s.startswith('|') or re.search(r'\d', re.sub(r'\[\[[^\]]*\]\]', '', s)):
                        warns.append((rel, 'uncited', '第 %d 行含數字但無引用：%s' % (ln, s[:80])))
            for rx, what in PRIV:
                for m in rx.finditer(line):
                    if what == 'IP 位址' and PRIV_ALLOW.fullmatch(m.group(0)) and m.group(0).count('.') < 3: continue
                    errors.append((rel, 'privacy', '%s：%s（第 %d 行）' % (what, m.group(0), ln)))
    for pid in pages:
        if pid not in SPECIAL and pid != 'overview' and pid not in linked:
            warns.append(('wiki/' + pid + '.md', 'link-broken', '孤立頁：沒有其他條目連到它'))
    ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    out = ROOT / 'checks' / ('lint-%s.md' % ts)
    out.parent.mkdir(exist_ok=True)
    lines = ['# Lint %s' % ts, '', '- 條目 %d 頁、引用 %d 處' % (len(pages), n_cites),
             '- 錯誤 %d、警告 %d' % (len(errors), len(warns)), '', '## 錯誤', '']
    lines += ['- [%s] %s：%s' % (t, f, m) for f, t, m in errors] or ['- 無']
    lines += ['', '## 警告', ''] + (['- [%s] %s：%s' % (t, f, m) for f, t, m in warns] or ['- 無'])
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    (ROOT / 'checks/lint-latest.json').write_text(json.dumps(
        {'ts': ts, 'pages': len(pages), 'cites': n_cites, 'errors': errors, 'warnings': warns, 'report': out.name},
        ensure_ascii=False, indent=1), encoding='utf-8')
    print('pages %d cites %d errors %d warnings %d -> %s' % (len(pages), n_cites, len(errors), len(warns), out.name))
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
