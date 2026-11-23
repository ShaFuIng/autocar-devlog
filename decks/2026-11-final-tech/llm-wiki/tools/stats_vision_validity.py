"""統計最終版實跑逐格紀錄中「視覺路徑有效／無效」的比例（依 lap_pos 路段）。

用法（唯讀，不修改輸入檔）：
    python -I tools/stats_vision_validity.py <pid.jsonl 路徑>

輸入：run-b541-20261123 的 pid.jsonl（raw/MANIFEST.tsv 中 kind=run、mode=external 的項目，55 MB，不複製進 raw）。
只讀 kind=='sample' 的列（＝控制端實際消費並送出命令的格；未被消費的相機格不在紀錄內）。

三層有效旗標（由上游到下游）：
  A 基準線 baseline   vision.path_diagnostic.junction.baseline_valid
                      camera-pair-v2 基準估計（左右白線配對／單線＋寬度）是否給出路徑
  B worker 選定       vision.path_diagnostic.junction.selected_valid
                      路口切換器（基準／透視走廊）選定後的有效性；預測路徑不算有效
  C 控制端最後        vision.valid
                      live_pid 再以虛線路線（dash_route）或坡頂中點（crest_midpoint）覆寫後的有效性；
                      覆寫來源記在 vision.selected_source
  C 無效的格交給 lost_policy（失線規則），其 proposal.reason 也一併統計。
路段名：proposal.lap_pos.seg（lap-pos 估計，非人工標註）。
最長連續無效：以相鄰 sample 的 vision.capture_at 計，跨路段連續也算同一段（記在起點路段）。
"""
import json
import sys
from collections import Counter, OrderedDict, defaultdict


def main(path):
    segs = OrderedDict()
    junction_src = defaultdict(Counter)
    sel_src = defaultdict(Counter)
    bad_reason = defaultdict(Counter)
    lost_reason = defaultdict(Counter)
    longest = defaultdict(float)
    tot = Counter()
    run_start = None  # (seg, t0) of the current final-invalid streak
    first_t = last_t = None
    timing = OrderedDict((k, []) for k in ('stage_ms.decode (ms)', 'stage_ms.model (ms)', 'stage_ms.path (ms)', 'stage_ms.queue (ms)',
                                           'inference_ms (ms)', 'control_age_s ×1000 (ms)', '相鄰 sample 取像間隔 (ms)'))
    with open(path, encoding='utf8') as f:
        for line in f:
            d = json.loads(line)
            if d.get('kind') != 'sample':
                continue
            v = d.get('vision') or {}
            p = d.get('proposal') or {}
            seg = (p.get('lap_pos') or {}).get('seg') or p.get('seg') or '(none)'
            pd = v.get('path_diagnostic') or {}
            j = pd.get('junction') or {}
            t = v.get('capture_at')
            sm = v.get('stage_ms') or {}
            for k in ('decode', 'model', 'path', 'queue'):
                if isinstance(sm.get(k), (int, float)):
                    timing[f'stage_ms.{k} (ms)'].append(sm[k])
            if isinstance(v.get('inference_ms'), (int, float)):
                timing['inference_ms (ms)'].append(v['inference_ms'])
            if isinstance(v.get('control_age_s'), (int, float)):
                timing['control_age_s ×1000 (ms)'].append(v['control_age_s'] * 1000)
            if last_t is not None and t is not None:
                timing['相鄰 sample 取像間隔 (ms)'].append((t - last_t) * 1000)
            first_t = t if first_t is None else first_t
            last_t = t
            s = segs.setdefault(seg, Counter())
            for c in (s, tot):
                c['n'] += 1
                if not j.get('baseline_valid'):
                    c['a_bad'] += 1
                if not j.get('selected_valid'):
                    c['b_bad'] += 1
                if not v.get('valid'):
                    c['c_bad'] += 1
            junction_src[seg][str(j.get('source'))] += 1
            sel_src[seg][str(v.get('selected_source'))] += 1
            if not j.get('selected_valid'):
                bad_reason[seg][(pd.get('road_state') or {}).get('reason') or '(none)'] += 1
            if not v.get('valid'):
                lost_reason[seg][p.get('reason') or '(none)'] += 1
                if run_start is None:
                    run_start = (seg, t)
                longest[run_start[0]] = max(longest[run_start[0]], t - run_start[1])
            else:
                run_start = None
    pct = lambda a, n: f'{a / n * 100:.1f}%'
    print(f'samples {tot["n"]}, capture span {last_t - first_t:.1f} s')
    print()
    print('| 路段 seg | 格數 | A 基準線無效 | B worker 選定無效 | C 控制端最後無效 | C 最長連續無效 (s) |')
    print('|---|---|---|---|---|---|')
    for seg, s in segs.items():
        n = s['n']
        print(f"| {seg} | {n} | {s['a_bad']}（{pct(s['a_bad'], n)}） | {s['b_bad']}（{pct(s['b_bad'], n)}） | "
              f"{s['c_bad']}（{pct(s['c_bad'], n)}） | {longest[seg]:.2f} |")
    n = tot['n']
    print(f"| 合計 | {n} | {tot['a_bad']}（{pct(tot['a_bad'], n)}） | {tot['b_bad']}（{pct(tot['b_bad'], n)}） | "
          f"{tot['c_bad']}（{pct(tot['c_bad'], n)}） | |")
    print()
    print('| 路段 seg | 路口來源 junction.source | 控制端覆寫 selected_source | B 無效原因 road_state.reason | C 無效時 proposal.reason |')
    print('|---|---|---|---|---|')
    fmt = lambda c: '、'.join(f'{k} {v}' for k, v in c.most_common()) or '—'
    for seg in segs:
        print(f'| {seg} | {fmt(junction_src[seg])} | {fmt(sel_src[seg])} | {fmt(bad_reason[seg])} | {fmt(lost_reason[seg])} |')
    # 附帶：worker 各階段耗時與控制資料年齡（同一批 sample）
    print()
    print('| 項目 | 中位數 | P90 | 格數 |')
    print('|---|---|---|---|')
    for name, vals in timing.items():
        if not vals:
            continue
        vs = sorted(vals)
        q = lambda f: vs[min(len(vs) - 1, int(f * (len(vs) - 1) + 0.5))]
        print(f'| {name} | {q(0.5):.1f} | {q(0.9):.1f} | {len(vs)} |')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main(sys.argv[1])
