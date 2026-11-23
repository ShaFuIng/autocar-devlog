"""統計 checks/loop-log.jsonl：各節點檢查／失敗次數、錯誤類型、每個問題的輪數。
用法：python tools/loop_stats.py   → 印出並寫 checks/loop-stats.md"""
import json, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / 'checks/loop-log.jsonl'


def main():
    rows = [json.loads(l) for l in LOG.read_text(encoding='utf-8').splitlines() if l.strip()]
    by_node = collections.defaultdict(lambda: [0, 0])
    by_type = collections.Counter(); by_target = collections.Counter()
    issues = collections.defaultdict(list)
    for r in rows:
        n = by_node[r['node']]; n[0] += 1
        if r['result'] == 'Fail':
            n[1] += 1; by_type[r.get('type') or '?'] += 1
            if r.get('retry_target'): by_target[r['retry_target']] += 1
        issues[r['issue']].append(r)
    lines = ['# Loop 統計', '', '共 %d 筆檢查紀錄、%d 個問題。' % (len(rows), len(issues)), '',
             '| 節點 | 檢查次數 | 失敗次數 |', '|---|---|---|']
    lines += ['| %s | %d | %d |' % (k, v[0], v[1]) for k, v in sorted(by_node.items())]
    lines += ['', '| 錯誤類型 | 次數 |', '|---|---|'] + ['| %s | %d |' % kv for kv in by_type.most_common()] or []
    lines += ['', '| 回退節點 | 次數 |', '|---|---|'] + ['| %s | %d |' % kv for kv in sorted(by_target.items())]
    lines += ['', '| 問題 | 輪數 | 最後結果 |', '|---|---|---|']
    for k, rs in issues.items():
        last = rs[-1]
        lines.append('| %s | %d | %s |' % (k, max(r.get('round', 1) for r in rs), last.get('recheck') or last['result']))
    out = '\n'.join(lines) + '\n'
    (ROOT / 'checks/loop-stats.md').write_text(out, encoding='utf-8')
    import sys
    sys.stdout.buffer.write(out.encode('utf-8'))


if __name__ == '__main__':
    main()
