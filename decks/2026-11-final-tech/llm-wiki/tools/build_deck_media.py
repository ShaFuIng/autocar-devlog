"""競賽技術簡報（autocar-devlog decks/2026-11-final-tech）用圖。只讀實跑紀錄，不連車、不改原始資料。
影像頁：run-1f77-20261119（11-19，有錄影；模型權重與最終版相同 8b802fa0，控制版本較早）。
控制頁：run-b541-20261123（11-23 最終版）pid.jsonl 逐格紀錄重繪。
隱私：影片上半部（場邊與路人）先模糊，再疊遮罩與路徑（沿用 devlog-media-20261116/build_media.py）。
用法：python build_deck_media.py [輸出資料夾]"""
import json, sys, base64, bisect, os, shutil, collections
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

E = 'D:/OneDrive/Desktop/自走車/Orin_Interface_v1/laptop_workbench/data/experiments'
VRUN = os.path.join(E, 'run-1f77-20261119')
CRUN = os.path.join(E, 'run-b541-20261123')
OUT = sys.argv[1] if len(sys.argv) > 1 else 'D:/OneDrive/Desktop/自走車/autocar-devlog/decks/2026-11-final-tech'
os.makedirs(OUT, exist_ok=True)
W, H = 640, 360
BG, PANEL, INK, MUT, LINE, ACC, WARM, RED = '#0a111a', '#101e2b', '#eef3f7', '#a6b8c8', '#293b4d', '#81e9c7', '#ffbe75', '#ff7a8a'
SEGN = {'start_straight': '起點直線', 'main_straight': '主直線', 'curve1': '彎1', 'diagonal_v': '斜線', 'curve2': '彎2',
        'circle_straight': '圓圈直線', 'left_bend': '左彎', 'curve3': '彎3', 'ramp': '上坡', 'top': '坡頂',
        'dashed_turn': '虛線轉彎', 'upper_straight': '上層直線', 'downhill': '下坡', 'bottom': '坡底', 'curve4': '彎4'}
fm.fontManager.addfont('C:/Windows/Fonts/msjh.ttc')
plt.rcParams['font.family'] = fm.FontProperties(fname='C:/Windows/Fonts/msjh.ttc').get_name()
plt.rcParams['axes.unicode_minus'] = False
STATS = {}


def F(s):
    return ImageFont.truetype('C:/Windows/Fonts/msjhbd.ttc', s)


def imwrite(path, im, params=()):
    ok, buf = cv2.imencode(os.path.splitext(path)[1], im, list(params))
    open(path, 'wb').write(buf.tobytes())


def to_pil(im):
    return Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB)).convert('RGBA')


def to_bgr(pil):
    return cv2.cvtColor(np.array(pil.convert('RGB')), cv2.COLOR_RGB2BGR)


def decode_mask(r, size):
    m = cv2.imdecode(np.frombuffer(base64.b64decode(r['vision']['mask_png']), np.uint8), cv2.IMREAD_GRAYSCALE)
    return cv2.resize(m, size, interpolation=cv2.INTER_NEAREST) > 0


def blur_top(im, frac=0.38):
    h = int(im.shape[0] * frac)
    k = (im.shape[1] // 12) | 1
    im = im.copy()
    im[:h] = cv2.GaussianBlur(im[:h], (k, k), 0)
    return im


def overlay(im, r, path=True, ends=False):
    im = blur_top(cv2.resize(im, (W, H), interpolation=cv2.INTER_AREA))
    v = r['vision']
    if v.get('mask_png'):
        m = decode_mask(r, (W, H))
        tint = im.copy()
        tint[m] = (150, 230, 60)
        im = cv2.addWeighted(tint, 0.45, im, 0.55, 0)
        cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(im, cs, -1, (150, 230, 60), 2, cv2.LINE_AA)
    if path and v.get('valid') and v.get('path'):
        p = np.array(v['path'], float) * [W / 1280, H / 720]
        cv2.polylines(im, [p.astype(np.int32)], False, (40, 200, 255), 3, cv2.LINE_AA)
        if ends:
            for q, c in ((p[-1], (255, 190, 117)), (p[0], (255, 122, 138))):
                cv2.circle(im, tuple(int(x) for x in q), 7, c[::-1], -1, cv2.LINE_AA)
    return im


def label(im, text, sub=None):
    pil = to_pil(im)
    ov = Image.new('RGBA', pil.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    w = d.textlength(text, font=F(20))
    d.rounded_rectangle([8, 8, 26 + w, 42], 7, fill=(10, 17, 26, 215))
    d.text((17, 10), text, font=F(20), fill=(238, 243, 247))
    if sub:
        w2 = d.textlength(sub, font=F(14))
        d.rounded_rectangle([8, H - 34, 24 + w2, H - 8], 6, fill=(10, 17, 26, 215))
        d.text((16, H - 32), sub, font=F(14), fill=(166, 184, 200))
    return to_bgr(Image.alpha_composite(pil, ov))


def load(run):
    S = []
    for l in open(os.path.join(run, 'pid.jsonl'), encoding='utf-8'):
        r = json.loads(l)
        if r.get('kind') == 'sample':
            S.append(r)
    return S


# ---------------- 影像頁（run-1f77） ----------------
def vision_pages():
    S = [r for r in load(VRUN) if r.get('vision') and r['vision'].get('mask_png') and (r['proposal'].get('lap_pos') or {}).get('seg')]
    frames = [json.loads(l) for l in open(os.path.join(VRUN, 'frames_001.jsonl'))]
    ft = [f['capture_monotonic'] for f in frames]
    cap = cv2.VideoCapture(os.path.join(VRUN, 'video_001.avi'))
    laps = collections.defaultdict(list)
    for i, r in enumerate(S):
        laps[r['proposal']['lap_pos']['lap']].append(i)
    lap = sorted(laps, key=lambda k: -len(laps[k]))[0]
    idx = laps[lap]

    def grab(seg, frac):
        k = [i for i in idx if S[i]['proposal']['lap_pos']['seg'] == seg]
        i = k[int(len(k) * frac)]
        t = S[i]['vision']['capture_at']
        j = bisect.bisect_left(ft, t)
        j = min(range(max(0, j - 2), min(len(ft), j + 2)), key=lambda q: abs(ft[q] - t))
        cap.set(cv2.CAP_PROP_POS_FRAMES, j)
        ok, im = cap.read()
        return S[i], im, abs(ft[j] - t)

    # P03 三連圖：彎 2 前（圓圈前的斜線末段，平地）
    r, im, dt = grab('diagonal_v', 0.85)
    raw = blur_top(cv2.resize(im, (W, H), interpolation=cv2.INTER_AREA))
    mk = cv2.cvtColor((decode_mask(r, (W, H)) * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
    ov = overlay(im, r, path=False)
    tri = np.hstack([label(raw, '① 相機原圖'), label(mk, '② 白線遮罩（模型輸出）'), label(ov, '③ 遮罩疊回原圖')])
    tri = cv2.resize(tri, (1200, int(1200 * H / (3 * W))), interpolation=cv2.INTER_AREA)
    imwrite(os.path.join(OUT, 'p03-seg-triptych.webp'), tri, [cv2.IMWRITE_WEBP_QUALITY, 82])
    STATS['p03'] = dict(lap=lap, seg='diagonal_v', s_m=r['proposal']['lap_pos']['s_m'], sync_ms=round(dt * 1000, 1),
                        model=r['vision'].get('model_id'), w=r['vision'].get('weights_sha256', '')[:8])

    # P04 路徑疊合：主直線與彎 1 前
    tiles = []
    for seg, fr, name in (('main_straight', 0.6, '主直線'), ('curve1', 0.5, '彎 1 彎中')):
        r, im, dt = grab(seg, fr)
        tiles.append(label(overlay(im, r, ends=True), name, '青線＝中心路徑；橘點＝最近點、紅點＝最遠點'))
    g = cv2.resize(np.hstack(tiles), (1200, int(1200 * H / (2 * W))), interpolation=cv2.INTER_AREA)
    imwrite(os.path.join(OUT, 'p04-path-overlay.webp'), g, [cv2.IMWRITE_WEBP_QUALITY, 82])

    # P05 失效情境：圓圈路口、上層虛線轉彎、下坡
    tiles = []
    for seg, fr, name in (('circle_straight', 0.3, '圓圈路口：交叉線'), ('dashed_turn', 0.5, '上層虛線轉彎'),
                          ('downhill', 0.5, '下坡：只見前方地面')):
        r, im, dt = grab(seg, fr)
        sub = '路徑有效' if r['vision'].get('valid') else '路徑無效'
        tiles.append(label(overlay(im, r), name, sub))
    g = cv2.resize(np.hstack(tiles), (1200, int(1200 * H / (3 * W))), interpolation=cv2.INTER_AREA)
    imwrite(os.path.join(OUT, 'p05-failure-frames.webp'), g, [cv2.IMWRITE_WEBP_QUALITY, 82])
    STATS['vision_lap'] = lap


# ---------------- 控制頁（run-b541） ----------------
def style(ax):
    ax.set_facecolor(PANEL)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(colors=MUT, length=0, labelsize=10)
    ax.grid(color=LINE, lw=.7)
    ax.set_axisbelow(True)


def fig(n, h=5.2):
    f, ax = plt.subplots(n, 1, figsize=(12, h), sharex=True, facecolor=BG, gridspec_kw={'hspace': .12})
    ax = np.atleast_1d(ax)
    for a in ax:
        style(a)
    return f, ax


def save(f, name, note):
    f.text(0.01, 0.005, note, color=MUT, fontsize=9)
    f.savefig(os.path.join(OUT, name), dpi=100, facecolor=BG, bbox_inches='tight')
    plt.close(f)


NOTE = 'run-b541（11-23 最終版）逐格紀錄重繪'


def segbands(ax, xs, segs, top=True):
    a = 0
    for k in range(1, len(xs) + 1):
        if k == len(xs) or segs[k] != segs[a]:
            for j, x in enumerate(ax):
                if (len([1 for _ in range(0)]) or True) and segs[a] in ('curve1', 'curve2', 'curve3', 'curve4', 'ramp', 'downhill', 'top'):
                    x.axvspan(xs[a], xs[k - 1], color='#1b3245', lw=0)
            if top and segs[a] and (xs[k - 1] - xs[a]) > 1.2:
                ax[0].text((xs[a] + xs[k - 1]) / 2, 1.01, SEGN.get(segs[a], segs[a]), transform=ax[0].get_xaxis_transform(),
                           ha='center', va='bottom', color=WARM if segs[a].startswith('curve') else MUT, fontsize=9)
            a = k


def control_pages():
    S = load(CRUN)
    P = [r['proposal'] for r in S]
    # P05：路徑無效比例（proposal.valid）
    cnt = collections.Counter(); bad = collections.Counter()
    for p in P:
        sg = p.get('seg') if p.get('seg') else ((p.get('lap_pos') or {}).get('seg'))
        sg = (p.get('lap_pos') or {}).get('seg') or 'none'
        cnt[sg] += 1
        if not p.get('valid'):
            bad[sg] += 1
    tot_bad = sum(bad.values()); tot = len(P)
    STATS['invalid'] = dict(total=tot, bad=tot_bad, pct=round(100 * tot_bad / tot, 2), by_seg={k: (bad[k], cnt[k]) for k in cnt if bad[k]})
    # 最長連續無效（以 t_send 計）
    run_s, best, t0 = 0, 0.0, None
    ts = [((p.get('inputs') or {}).get('t_send')) for p in P]
    for p, t in zip(P, ts):
        if not p.get('valid'):
            if t0 is None and t is not None:
                t0 = t
            if t is not None and t0 is not None:
                best = max(best, t - t0)
        else:
            if t0 is not None and t is not None:
                best = max(best, t - t0)
            t0 = None
    STATS['invalid']['longest_s_approx'] = round(best, 3)
    order = [k for k in SEGN if k in cnt] + [k for k in cnt if k not in SEGN]
    f, ax = plt.subplots(figsize=(12, 4.2), facecolor=BG); style(ax)
    pct = [100 * bad[k] / cnt[k] for k in order]
    ax.bar(range(len(order)), pct, color=[RED if v > 0 else LINE for v in pct], width=.65)
    for i, k in enumerate(order):
        ax.text(i, pct[i] + 0.05, '%d/%d' % (bad[k], cnt[k]), ha='center', color=MUT, fontsize=8.5)
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels([SEGN.get(k, '未定位' if k == 'none' else k) for k in order], color=INK, fontsize=10)
    ax.set_ylabel('路徑無效格比例（%）', color=MUT)
    ax.set_title('全程 %d 格中 %d 格路徑無效（%.2f%%）' % (tot, tot_bad, 100 * tot_bad / tot), color=INK, fontsize=12, loc='left')
    save(f, 'p05-invalid-by-seg.png', NOTE + '；無效＝控制端 valid 為否；柱上數字＝無效格/該路段總格')

    # 圈分組
    L = collections.defaultdict(list)
    for i, p in enumerate(P):
        lp = p.get('lap_pos')
        if lp and p.get('inputs'):
            L[lp['lap']].append(i)
    full = [k for k in sorted(L) if k >= 1 and len(L[k]) > 1000]
    lap = full[0] if full else sorted(L, key=lambda k: -len(L[k]))[0]
    idx = L[lap]
    STATS['ctrl_laps'] = {k: len(v) for k, v in L.items()}
    STATS['ctrl_lap_used'] = lap
    s = np.array([P[i]['lap_pos']['s_m'] for i in idx])
    gz = np.array([P[i]['inputs']['gz'] for i in idx])
    pit = np.array([((P[i].get('imu_boost') or {}).get('pitch_rel_deg', np.nan)) for i in idx], float)
    sg = [P[i]['lap_pos']['seg'] for i in idx]
    f, ax = fig(2, 5.4)
    segbands(ax, s, sg)
    ax[0].plot(s, pit, color=ACC, lw=1.4)
    ax[0].set_ylabel('相對俯仰（°）', color=MUT)
    ax[1].plot(s, gz, color=WARM, lw=1.1)
    ax[1].set_ylabel('車頭轉速 gz（°/s）', color=MUT)
    ax[1].set_xlabel('圈內位置（m）', color=MUT)
    save(f, 'p06-imu-lap.png', NOTE + '，第 %d 圈；俯仰＝imu_boost.pitch_rel_deg（相對平地基準），gz＝inputs.gz；色帶＝彎道與坡道' % lap)

    # P07 路口：arc2_blind 作用段（取 idx 內第一段）
    k = [i for i in idx if P[i].get('arc2_blind')]
    seg_i = [k[0]]
    for i in k[1:]:
        if i - seg_i[-1] <= 2:
            seg_i.append(i)
        else:
            break
    a0, a1 = max(0, seg_i[0] - 25), min(len(P) - 1, seg_i[-1] + 25)
    rng = [i for i in range(a0, a1 + 1) if P[i].get('inputs')]
    t = np.array([P[i]['inputs']['t_send'] for i in rng]); t = t - t[0]
    st = np.array([P[i]['steer_us'] for i in rng], float)
    pidu = np.array([((P[i].get('arc2_blind') or {}).get('pid_steer_us', np.nan)) for i in rng], float)
    dpsi = np.array([((P[i].get('arc2_blind') or {}).get('dpsi', np.nan)) for i in rng], float)
    gzz = np.array([P[i]['inputs']['gz'] for i in rng])
    states = [((P[i].get('arc2_blind') or {}).get('state') or '未作用') for i in rng]
    f, ax = fig(3, 6.2)
    ax[0].plot(t, dpsi, color=ACC, lw=1.6, label='航向差 Δψ（arc2_blind.dpsi）')
    ax[0].plot(t, gzz, color=MUT, lw=1, alpha=.7, label='gz（°/s）')
    ax[0].legend(facecolor=PANEL, edgecolor=LINE, labelcolor=INK, fontsize=9, loc='upper right')
    ax[0].set_ylabel('°  /  °/s', color=MUT)
    ax[1].plot(t, st, color=WARM, lw=1.6, label='實送舵量 steer_us')
    ax[1].plot(t, pidu, color=RED, lw=1.1, ls='--', label='PID 原本要的 pid_steer_us')
    ax[1].axhline(1445, color=MUT, lw=.8, ls=':')
    ax[1].legend(facecolor=PANEL, edgecolor=LINE, labelcolor=INK, fontsize=9, loc='upper right')
    ax[1].set_ylabel('µs', color=MUT)
    pal = {'未作用': LINE}
    cols = [ACC, WARM, RED, '#7fb2ff', '#c79bff']
    for st_ in states:
        if st_ not in pal:
            pal[st_] = cols[(len(pal) - 1) % len(cols)]
    for j in range(len(t) - 1):
        ax[2].axvspan(t[j], t[j + 1], color=pal[states[j]], lw=0)
    ax[2].set_yticks([])
    for n_, c in pal.items():
        ax[2].plot([], [], color=c, lw=8, label=n_)
    ax[2].legend(ncol=len(pal), facecolor=PANEL, edgecolor=LINE, labelcolor=INK, fontsize=9, loc='upper left')
    ax[2].set_ylabel('層狀態', color=MUT)
    ax[2].set_xlabel('時間（s）', color=MUT)
    lp0 = P[seg_i[0]]['lap_pos']
    save(f, 'p07-junction.png', NOTE + '，第 %d 圈 %s 路口段（arc2_blind 作用 %d 格）' % (lp0['lap'], SEGN.get(lp0['seg'], lp0['seg']), len(seg_i)))
    STATS['p07'] = dict(lap=lp0['lap'], seg=lp0['seg'], s_m=lp0['s_m'], frames=len(seg_i), states=sorted(set(states)),
                        dpsi_max=float(np.nanmax(np.abs(dpsi))))

    # P08 彎 2：lap_ff curve==c2
    k = [i for i in idx if (P[i].get('lap_ff') or {}).get('curve') == 'c2']
    rng = [i for i in range(max(0, k[0] - 10), min(len(P), k[-1] + 15)) if P[i].get('inputs')]
    t = np.array([P[i]['inputs']['t_send'] for i in rng]); t = t - t[0]
    band = [((P[i].get('lap_ff') or {}).get('band') or {}) for i in rng]
    turned = np.array([b.get('turned_deg', np.nan) for b in band], float)
    prof = np.array([b.get('prof_us', np.nan) for b in band], float)
    st = np.array([P[i]['steer_us'] for i in rng], float)
    err = np.array([P[i].get('error', np.nan) if P[i].get('error') is not None else np.nan for i in rng], float)
    f, ax = fig(3, 6.4)
    ax[0].plot(t, turned, color=ACC, lw=1.8)
    ax[0].set_ylabel('已轉角度（°）', color=MUT)
    ax[1].plot(t, prof, color=ACC, lw=1.6, label='前饋目標 band.prof_us')
    ax[1].plot(t, st, color=WARM, lw=1.4, label='實送舵量 steer_us')
    ax[1].axhline(1445, color=MUT, lw=.8, ls=':')
    ax[1].legend(facecolor=PANEL, edgecolor=LINE, labelcolor=INK, fontsize=9, loc='lower right')
    ax[1].set_ylabel('µs', color=MUT)
    ax[2].plot(t, err, color=RED, lw=1.3)
    ax[2].axhline(0, color=MUT, lw=.8, ls=':')
    ax[2].set_ylabel('近誤差 error', color=MUT)
    ax[2].set_xlabel('時間（s）', color=MUT)
    save(f, 'p08-c2-band.png', NOTE + '，第 %d 圈彎 2（lap_ff 帶狀前饋作用 %d 格）' % (lap, len(k)))
    STATS['p08'] = dict(lap=lap, frames=len(k), turned_max=float(np.nanmax(turned)), steer_max=float(np.nanmax(st)),
                        dur_s=float(P[k[-1]]['inputs']['t_send'] - P[k[0]]['inputs']['t_send']))

    # P09 坡道：ramp 起到 land4 結束後 1 m
    r0 = [i for i in idx if P[i]['lap_pos']['seg'] == 'ramp'][0]
    l4 = [i for i in idx if P[i].get('land4')]
    r1 = l4[-1] if l4 else [i for i in idx if P[i]['lap_pos']['seg'] == 'downhill'][-1]
    rng = [i for i in range(r0 - 10, min(len(P), r1 + 20)) if P[i].get('lap_pos') and P[i].get('inputs')]
    o = np.array([P[i]['lap_pos']['odo_m'] for i in rng]); o = o - P[r0]['lap_pos']['odo_m']
    pit = np.array([((P[i].get('imu_boost') or {}).get('pitch_rel_deg', np.nan)) for i in rng], float)
    psi = np.array([((P[i].get('land4') or {}).get('psi', np.nan)) for i in rng], float)
    st = np.array([P[i]['steer_us'] for i in rng], float)
    l4s = [((P[i].get('land4') or {}).get('state')) for i in rng]
    sg = [P[i]['lap_pos']['seg'] for i in rng]
    f, ax = fig(3, 6.4)
    segbands(ax, o, sg)
    ax[0].plot(o, pit, color=ACC, lw=1.6)
    ax[0].set_ylabel('相對俯仰（°）', color=MUT)
    ax[1].plot(o, psi, color=WARM, lw=1.6)
    ax[1].set_ylabel('land4.psi（°）', color=MUT)
    ax[2].plot(o, st, color=INK, lw=1.4)
    ax[2].axhline(1445, color=MUT, lw=.8, ls=':')
    on = [j for j, x in enumerate(l4s) if x]
    if on:
        for a in ax:
            a.axvspan(o[on[0]], o[on[-1]], color=ACC, alpha=.08, lw=0)
    ax[2].set_ylabel('實送舵量（µs）', color=MUT)
    ax[2].set_xlabel('自上坡起點的里程（m）', color=MUT)
    save(f, 'p09-slope.png', NOTE + '，第 %d 圈上坡→坡頂→上層→下坡→落地；淡綠底＝land4 有紀錄的範圍；land4 狀態：%s' % (lap, '/'.join(sorted(set(x for x in l4s if x)))))
    STATS['p09'] = dict(lap=lap, land4_states=sorted(set(x for x in l4s if x)), pitch_min=float(np.nanmin(pit)), pitch_max=float(np.nanmax(pit)))

    # P13 推論耗時與控制資料年齡
    inf, age, stage = [], [], collections.defaultdict(list)
    for r in S:
        v = r.get('vision')
        if not v:
            continue
        if v.get('inference_ms') is not None:
            inf.append(v['inference_ms'])
        if v.get('consumed_at') and v.get('capture_at'):
            age.append(1000 * (v['consumed_at'] - v['capture_at']))
        for kk, vv in (v.get('stage_ms') or {}).items():
            if isinstance(vv, (int, float)):
                stage[kk].append(vv)
    inf, age = np.array(inf), np.array(age)
    STATS['p13'] = dict(n=len(inf), inf_med=round(float(np.median(inf)), 1), inf_p90=round(float(np.percentile(inf, 90)), 1),
                        age_n=len(age), age_med=round(float(np.median(age)), 1), age_p90=round(float(np.percentile(age, 90)), 1),
                        stage_med={kk: round(float(np.median(vv)), 1) for kk, vv in stage.items()})
    f, ax = plt.subplots(1, 2, figsize=(12, 4.2), facecolor=BG)
    for a in ax:
        style(a)
    ax[0].hist(inf, bins=50, color=ACC)
    ax[0].axvline(np.median(inf), color=WARM, lw=1.5)
    ax[0].set_title('vision.inference_ms（中位 %.1f ms，n=%d）' % (np.median(inf), len(inf)), color=INK, fontsize=11, loc='left')
    ax[0].set_xlabel('ms', color=MUT)
    ax[1].hist(age, bins=50, color=WARM)
    ax[1].axvline(np.median(age), color=ACC, lw=1.5)
    ax[1].set_title('擷取→控制消費（consumed_at−capture_at，中位 %.1f ms）' % np.median(age), color=INK, fontsize=11, loc='left')
    ax[1].set_xlabel('ms', color=MUT)
    save(f, 'p13-inference-hist.png', NOTE + '；兩者皆為 Orin 同一時鐘')


def track_map():
    src = 'D:/OneDrive/Desktop/自走車/跑道地圖_統一版_01-12.webp'
    im = Image.open(src)
    if im.width > 1200:
        im = im.resize((1200, int(im.height * 1200 / im.width)), Image.LANCZOS)
    im.save(os.path.join(OUT, 'track-map.webp'), quality=85)


if __name__ == '__main__':
    track_map()
    control_pages()
    vision_pages()
    print(json.dumps(STATS, ensure_ascii=False, indent=1, default=str))
