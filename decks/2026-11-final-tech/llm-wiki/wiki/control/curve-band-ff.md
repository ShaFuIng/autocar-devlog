---
id: control/curve-band-ff
title: 急彎控制：位置觸發的帶狀前饋（彎 1～彎 4）
status: implemented
sources:
  - raw/project/snapshot-20261123d/lap_ff.py
  - raw/project/snapshot-20261123d/lap_ff.json
  - raw/project/snapshot-20261123d/arc2.py
  - raw/project/snapshot-20261123d/arc2.json
  - raw/project/snapshot-20261123d/live_pid.py
  - raw/project/snapshot-20261123d/single_centre.py
  - raw/project/snapshot-20261123d/single_centre.json
  - raw/project/snapshot-20261123d/curve_ff.py
  - raw/project/snapshot-20261123d/curve_ff.json
  - raw/project/snapshot-20261123d/curve_map.py
  - raw/project/snapshot-20261123d/curve_map.json
  - raw/project/snapshot-20261123d/curve_trim.py
  - raw/project/snapshot-20261123d/curve_trim.json
  - raw/project/snapshot-20261123d/gain_schedule.py
  - raw/project/snapshot-20261123d/gain_schedule.json
  - raw/project/snapshot-20261123d/arc_lat.json
  - raw/project/snapshot-20261123d/_extra/start_params.json
  - raw/records/logs/AGENTS.md
verified_against: snapshot-20261123d
updated: 2026-11-23
---

# 急彎控制：帶狀前饋

## 一句話結論

四個右彎各由一個「位置觸發、依已轉角度查表」的帶狀前饋層決定舵量：彎 1、彎 2 由 lap_ff 全權（own_after_deg 0），彎 3 由 arc2.c3 的距離帶（x-band）在 C3s+0.9～4.05 m 全權並在尾段加上限，彎 4 由 lap_ff4 在落地後接手；curve_ff、curve_map、curve_trim、gain_schedule 是輔助層 [src: raw/project/snapshot-20261123d/lap_ff.json#key=curves.c1.band.own_after_deg] [src: raw/project/snapshot-20261123d/lap_ff.json#key=curves.c2.band.own_after_deg] [src: raw/project/snapshot-20261123d/arc2.json#key=c3.xband] [src: raw/project/snapshot-20261123d/lap_ff.json#key=c4.band.own]。

## 內容

名詞：
- 帶狀（band）：以「進彎前直線的 IMU 航向」為零點，量出「已轉角度 tb」，再依 tb 查表得到這個角度應有的曲率 κ 與相機誤差應有值 e_c，組成前饋舵量 [src: raw/project/snapshot-20261123d/lap_ff.py#L194-L197]。
- 全權（own）：輸出直接等於帶狀目標，PID 鏈的值只作為輸入、被上下夾住 [src: raw/project/snapshot-20261123d/lap_ff.py#L169-L171] [src: raw/project/snapshot-20261123d/lap_ff.py#L280]。
- 地標 C4e／C1e／C2e／C3s 等由 lap_pos 判定，見 [[control/lap-position]]；彎道編號對照見 [[overview]]。

### 為什麼不用單純的相機 PID
- 相機 PID 的前瞻約 0.85 m、場景到輪子延遲約 0.36 s；舵量只在幾何起點附近才開始上升，在地標處衝到 1800～2048，之後又掉回 1560～1570，形成脈衝（彎 2 每次都到 2048）[src: raw/project/snapshot-20261123d/lap_ff.py#L3-L6]。
- 置中的車在彎內看到 e≈+0.5，所以直接加前饋會切內；因此先做成「下限（floor）」，再演進成帶狀全權 [src: raw/project/snapshot-20261123d/lap_ff.py#L7-L10]。

### 在層表中的位置
- 順序：curve_ff → lap_ff → arc2_flat（含 arc2.c3 與兩個路口 blind）→ curve_trim → arc_lat → 速度群組 [src: raw/project/snapshot-20261123d/live_pid.py#L2262-L2267]。
- 彎 4 的 lap_ff4 排在 bottom_owner 之後、arc2_land 與 land4 之前 [src: raw/project/snapshot-20261123d/live_pid.py#L2285-L2289]。
- 會蓋過 lap_ff 的後段層：curve_trim（只在彎 1）、速度相關層不改舵量；下坡各層只在下坡窗口；jump_guard 在右舵時可能保持上一次送出值；之後還有輸出端間隙補償（見 [[control/play-comp]]）[src: raw/project/snapshot-20261123d/live_pid.py#L2271-L2292]。
- lap_ff 的適用條件：正常 PID 格、平地 WAIT_CLIMB、正常路徑來源、不在下坡窗口、不在 crossing_pass 窗口 [src: raw/project/snapshot-20261123d/live_pid.py#L1276]。

### 彎 1、彎 2：lap_ff 帶狀全權
- 觸發：lap_pos 未遺失、最後地標為彎道前一個地標，且距離落在 gap_m＋win_m 窗內；窗內第一個「遠處預覽誤差 ≥ 0.4 且近處誤差 ≥ −0.05」的有效格觸發（FAR）；彎 2 另有位置備援 pos_m −0.35（POS）；每個地標實例只觸發一次 [src: raw/project/snapshot-20261123d/lap_ff.py#L85-L107] [src: raw/project/snapshot-20261123d/lap_ff.json#key=far_on] [src: raw/project/snapshot-20261123d/lap_ff.json#key=curves.c2.pos_m]。
- 觸發保護：車頭比直線基準偏左超過 4°（trig_head_min_deg −4）時不接受 FAR 觸發 [src: raw/project/snapshot-20261123d/lap_ff.py#L235-L241] [src: raw/project/snapshot-20261123d/lap_ff.json#key=curves.c2.band.trig_head_min_deg]。
- 彎 1 窗：錨 C4e、gap 10.74 m、win [−1.8, 1.2]；第 1 圈從起點起跑時改用 START 偽錨點 gap 3.2 m、win [−1.2, 1.0]、直線基準取起跑後 0.4～1.8 m [src: raw/project/snapshot-20261123d/lap_ff.json#key=curves.c1.gap_m] [src: raw/project/snapshot-20261123d/lap_ff.json#key=curves.c1.start] [src: raw/project/snapshot-20261123d/lap_ff.py#L215-L217]。
- 彎 2 窗：錨 C1e、gap 11.94 m、win [−1.2, 0.6] [src: raw/project/snapshot-20261123d/lap_ff.json#key=curves.c2.gap_m]。
- 直線基準 plat：同一地標實例在 ref_win 內的 IMU 航向平均（彎 1 [3.0, 8.0] m、彎 2 [4.0, 9.0] m）；tb＝plat − 目前 IMU 航向 [src: raw/project/snapshot-20261123d/lap_ff.py#L219-L233] [src: raw/project/snapshot-20261123d/lap_ff.py#L248-L254] [src: raw/project/snapshot-20261123d/lap_ff.json#key=curves.c1.band.ref_win]。
- 漸入：觸發後延遲 delay_m（彎 1 0.3 m、彎 2 用全域 0.15 m），再以 ramp_m（彎 1 0.2 m、彎 2 0.25 m）線性升到 1 [src: raw/project/snapshot-20261123d/lap_ff.py#L143-L144] [src: raw/project/snapshot-20261123d/lap_ff.json#key=curves.c1.delay_m] [src: raw/project/snapshot-20261123d/lap_ff.json#key=delay_m]。
- 結束：帶狀 tb ≥ end_deg 或觸發後距離 ≥ max_m；彎 1 band end_deg 400（實際不會到）→ 由 max_m 4.7 m 結束；彎 2 為 tb ≥ 202° 或 5.8 m；之後 fade_m 0.5 m 淡出，釋放每格最多 max_drop_us 60 µs [src: raw/project/snapshot-20261123d/lap_ff.py#L151-L156] [src: raw/project/snapshot-20261123d/lap_ff.json#key=curves.c1.max_m] [src: raw/project/snapshot-20261123d/lap_ff.json#key=curves.c2.band.end_deg] [src: raw/project/snapshot-20261123d/lap_ff.json#key=max_drop_us]。
- 取消：no_cam_cancel true＝不因相機偏左取消；觸發後 check_m 1.3 m 仍轉不到 10° 則取消（NOT_TURNING）[src: raw/project/snapshot-20261123d/lap_ff.py#L146-L150] [src: raw/project/snapshot-20261123d/lap_ff.json#key=no_cam_cancel]。
- 彎內相機閘門：gate_after_deg 999＝實際不啟用 [src: raw/project/snapshot-20261123d/lap_ff.json#key=gate_after_deg]。
- 遺失格：帶狀未結束時，最多 1.0 s 用不含相機項的 profile＋陀螺儀項保持 [src: raw/project/snapshot-20261123d/lap_ff.py#L285-L308]，見 [[control/lost-path]]。

### 彎 3：arc2.c3（LapFF4 區塊＋x-band＋尾段上限）
- 觸發：錨 C3s，窗 win_m [0, 1.0]（自 C3s 起算，lap_pos 首次看到約在 0.52～0.69 m）[src: raw/project/snapshot-20261123d/arc2.json#L295-L305] [src: raw/project/snapshot-20261123d/arc2.json#L1146]。
- 基礎下限：target＝clip(c_eff + 0.7·κ(x)/g(v), 中心, cap_us)，floor＝PID＋a·max(0, target−PID)；κ 表為 70 次彎 3 中位數，x ≥ 4.925 m 起為 0 [src: raw/project/snapshot-20261123d/lap_ff.py#L525-L528] [src: raw/project/snapshot-20261123d/arc2.json#L412-L413] [src: raw/project/snapshot-20261123d/arc2.json#L545-L546]。
- x-band（距離帶，彎 3 前段的主控）：權重 w_x 在 0.6→0.9 m 升到 1、0.9～4.05 m 為 1、4.05→4.35 m 降到 0；近處誤差由 0.92 升到 1.00 時全權比例降到 0 [src: raw/project/snapshot-20261123d/arc2.json#L790] [src: raw/project/snapshot-20261123d/arc2.json#L1030-L1031] [src: raw/project/snapshot-20261123d/lap_ff.py#L637-L638]。命令＝平順路徑前饋 u_x＋航向項＋橫向位置項＋相機項＋陀螺儀項，速率限制 700 µs/s [src: raw/project/snapshot-20261123d/lap_ff.py#L606-L638] [src: raw/project/snapshot-20261123d/arc2.json#L1027]。
- 橫向位置項用 arc_lat 量到的 y（上一格），所以 arc_lat 雖然四彎都是 control false（不出命令），它的量測仍經 x-band 進入彎 3 控制 [src: raw/project/snapshot-20261123d/live_pid.py#L1387] [src: raw/project/snapshot-20261123d/live_pid.py#L1526] [src: raw/project/snapshot-20261123d/arc_lat.json#key=c3.control]。
- 尾段上限 top：C3s+4.95～5.85 m 內，最終舵量 ≤ 表值（1760→1640→1600 µs），每格最多降 25 µs、回升 150 µs；近處誤差 ≥ 0.8 或少轉 10° 以上則本次放手；從不提高舵量 [src: raw/project/snapshot-20261123d/arc2.json#L547-L574] [src: raw/project/snapshot-20261123d/lap_ff.py#L426-L466]。
- 坡腳：pitch_max 3°，俯仰超過即取消（彎 3 在坡腳結束）[src: raw/project/snapshot-20261123d/arc2.json#key=c3.pitch_max]。
- 適用條件同 lap_ff；彎 3 的 lap_ff.curves.c3 已關（enabled false），由 arc2.c3 取代 [src: raw/project/snapshot-20261123d/lap_ff.json#key=curves.c3.enabled] [src: raw/project/snapshot-20261123d/live_pid.py#L1384-L1391]。

### 彎 4：lap_ff4（落地後）
- 觸發錨點：LAND8（備援 DOWN+2.32 m），窗 [−0.3, 1.0] m [src: raw/project/snapshot-20261123d/lap_ff.json#key=c4.anchors] [src: raw/project/snapshot-20261123d/lap_ff.json#key=c4.win_m]。
- 帶狀基準：lap_pos 錨點為 DOWN、距離 0.1～1.9 m 的下坡直線平均 IMU 航向 [src: raw/project/snapshot-20261123d/lap_ff.json#key=c4.band.ref_win] [src: raw/project/snapshot-20261123d/lap_ff.py#L555-L558]。
- 帶狀自落地後 x0_m 1.2 m 起以 0.3 m 漸入；全權比例 own 自 1.5 m 起以 0.6 m 漸入，近處誤差 0.70→0.85 時降到 0 [src: raw/project/snapshot-20261123d/lap_ff.json#key=c4.band.x0_m] [src: raw/project/snapshot-20261123d/lap_ff.json#key=c4.band.own] [src: raw/project/snapshot-20261123d/lap_ff.py#L343-L350]。
- 結束：tb ≥ 193° 或 10.5 m [src: raw/project/snapshot-20261123d/lap_ff.json#key=c4.band.end_deg] [src: raw/project/snapshot-20261123d/lap_ff.json#key=c4.band.max_m]。
- 0～1.2 m（＋交還 0.3 m）由 land4 的 land 段全權，lap_ff4 的結果只是其輸入，見 [[control/slope-downhill]]。

### 輔助層
- 【現役】curve_ff（相機誤差大時的下限）：誤差 ≥ on_err 且（路徑向右彎 ≥ 15° 或車在右轉且非擺盪）時武裝，舵量至少為中心 + frac·0.9·(max_us−中心)，frac 由 on_err→full_err 從 0 升到 1，誤差 < off_err 解除 [src: raw/project/snapshot-20261123d/curve_ff.py#L6-L8] [src: raw/project/snapshot-20261123d/curve_ff.py#L10-L20]。彎 1、彎 2 用 by_curve 0.65／1.0／0.5，其他 0.55／0.85／0.4 [src: raw/project/snapshot-20261123d/curve_ff.json#key=by_curve] [src: raw/project/snapshot-20261123d/curve_ff.json#key=on_err]。彎 3 下限另受 CURVE3_FF_CAP_US 1850 上限（經 single_centre 平移）[src: raw/project/snapshot-20261123d/live_pid.py#L146-L148] [src: raw/project/snapshot-20261123d/live_pid.py#L1258-L1259]。在 lap_ff 之前，全權區內會被帶狀覆蓋。
- 【現役】curve_map（彎道角度地圖）：不直接出命令；依陀螺儀判斷「第幾個彎、轉了幾度」，未轉完前給 yaw_inner 轉速下限 20 deg/s，並提供 FLOOR／RELEASED 狀態給 curve_smooth、weave 判斷等 [src: raw/project/snapshot-20261123d/curve_map.py#L1-L18] [src: raw/project/snapshot-20261123d/live_pid.py#L962-L973]。彎角表以 json 為準：起跑後 map_start 140／195／268°、下坡後 map_after_down 145／140／195／268° [src: raw/project/snapshot-20261123d/curve_map.json#L1]。
- 【現役】curve_trim（只開彎 1）：C1s+0.4～2.6 m 內舵量減去查表值（0.8～2.3 m 為 30 µs），不低於中心+60 µs；誤差 ≥ 0.9 放手；彎 3 區塊 enabled false [src: raw/project/snapshot-20261123d/curve_trim.json#key=curves.c1.table] [src: raw/project/snapshot-20261123d/curve_trim.json#key=curves.c3.enabled] [src: raw/project/snapshot-20261123d/curve_trim.py#L11-L19]。說明文字寫 NOT deployed，但 json 開啟且主程式呼叫，以程式為準 [src: raw/project/snapshot-20261123d/curve_trim.py#L1] [src: raw/project/snapshot-20261123d/live_pid.py#L2265]。
- 【現役】gain_schedule：上一格速度層 PWM 高於 ref_pwm 19.6 時，舵量偏移乘 k＝max(0.57, 19.6/PWM)；上坡、下坡、航向保持、虛線轉彎、特殊路徑來源格不套用；右轉超過 +240 µs 時逐漸取消縮減 [src: raw/project/snapshot-20261123d/gain_schedule.py#L24-L29] [src: raw/project/snapshot-20261123d/gain_schedule.json#L1] [src: raw/project/snapshot-20261123d/live_pid.py#L934-L948]。它在 yaw_group 之前，帶狀全權區內不影響最終值。
- 【只記錄】arc_lat：四彎 control false，只記錄橫向位置，不出命令 [src: raw/project/snapshot-20261123d/arc_lat.json#key=c1.control]，見 [[control/disabled-layers]]。

### single_centre 對本頁數值的改寫
- single_centre.json enabled true：每次起跑時把「意指直行點」的數值改成共用中心，把「以 1480 為基準寫的絕對上限」改成 中心 + (值 − 1480) [src: raw/project/snapshot-20261123d/single_centre.json#key=enabled] [src: raw/project/snapshot-20261123d/single_centre.py#L6-L15]。
- 最終版共用中心 1445 [src: raw/project/snapshot-20261123d/_extra/start_params.json#key=center_us]，因此（推算，＝1445＋(值−1480)）：lap_ff c_eff_us 1490→1445；curves.c1／c2 cap 1800→1765；band cap 1950→1915；c4 cap 1720→1685；c4.band cap 1780→1745；arc2.c3 cap 1750→1715；CURVE3_FF_CAP 1850→1815 [src: raw/project/snapshot-20261123d/single_centre.py#L86-L117] [src: raw/project/snapshot-20261123d/live_pid.py#L146]。
- **arc2.c3.top 的絕對表（1760／1640／1600）不在 single_centre 改寫範圍**：apply_arc2 對 c3 只改 _c_eff_us、cap_us、band.cap_us，top 表照原值使用 [src: raw/project/snapshot-20261123d/single_centre.py#L97-L117] [src: raw/project/snapshot-20261123d/lap_ff.py#L448]。以中心 1445 計，1600＝中心＋155（推算）。

## 公式與參數

**lap_ff 帶狀目標（彎 1、彎 2）** [src: raw/project/snapshot-20261123d/lap_ff.py#L260-L283]：
```
κ    = κ_turn(tb)                               （deg/m，查表）
prof = c_eff + frac·κ / g(v_ref)
e_c  = e_c_turn(tb)                             （查表，取代 e_c·κ/κ_max）
et   = clip(k_e·(near − e_c), −e_lo, +e_hi)
gt   = clip(k_gz·(gz + v·κ), ±gz_lim)
tgt  = prof + et + gt，夾在 [中心 + own_lo, min(cap, max_us)]
own（tb ≥ own_after_deg）：上限 = tgt，且 tgt 另被 hi = prof + m_hi_us 夾住 → a = 1 時輸出 = min(tgt, prof + m_hi_us)（c1／c2 的 m_hi_us 140、c4 120）
out  = 中心 + a·(tgt − 中心) 與 PID 取大，再被 own 上限往下拉（a = 漸入×淡出）
```
[src: raw/project/snapshot-20261123d/lap_ff.py#L162-L173]

| 參數 | 第一彎 | 第二彎 | 性質 |
|---|---|---|---|
| κ_turn（deg/m） | 0～28° 36.2、46～100° 40.9，100° 起遞減（113° 39.0、120° 35、130° 25） [src: raw/project/snapshot-20261123d/lap_ff.json#key=curves.c1.band.kappa_turn] | 0° 30、30° 33.5、60～120° 42.4、150～184° 40、204° 0 [src: raw/project/snapshot-20261123d/lap_ff.json#key=curves.c2.band.kappa_turn] | 實測值修整後的調參值 |
| e_c_turn | 0° 0.3 → 40～110° 0.62 → 170° 0.05 [src: raw/project/snapshot-20261123d/lap_ff.json#key=curves.c1.band.e_c_turn] | 0° 0.3 → 83° 0.75 → 216° 0.1 [src: raw/project/snapshot-20261123d/lap_ff.json#key=curves.c2.band.e_c_turn] | 實測值（靜態置中量測）修整 |
| k_e／e_lo／e_hi | 220／250／150 µs [src: raw/project/snapshot-20261123d/lap_ff.json#key=curves.c1.band.k_e_us] | 220／250／150 µs [src: raw/project/snapshot-20261123d/lap_ff.json#key=curves.c2.band.k_e_us] | 調參值 |
| k_gz／gz_lim | 1.5／60 µs [src: raw/project/snapshot-20261123d/lap_ff.json#key=curves.c1.band.k_gz_us] | 1.5／60 µs [src: raw/project/snapshot-20261123d/lap_ff.json#key=curves.c2.band.gz_lim_us] | 調參值 |
| v_ref（profile 與陀螺儀項用的固定車速） | 1.1 m/s [src: raw/project/snapshot-20261123d/lap_ff.json#key=curves.c1.band.v_ref] | 1.08 m/s [src: raw/project/snapshot-20261123d/lap_ff.json#key=curves.c2.band.v_ref] | 調參值 |
| own_lo_us | −120 [src: raw/project/snapshot-20261123d/lap_ff.json#key=curves.c1.band.own_lo_us] | 無（＝0） | 調參值 |
| cap_us（帶狀） | 1950，起跑時改為 1915（推算） [src: raw/project/snapshot-20261123d/lap_ff.json#key=curves.c1.band.cap_us] | 同左 | 調參值 |
| frac／c_eff_us | 1.0／1490（起跑時改為中心 1445） [src: raw/project/snapshot-20261123d/lap_ff.json#key=frac] [src: raw/project/snapshot-20261123d/lap_ff.json#key=c_eff_us] | 同左 | 設計假設 |

g(v)（deg/m per µs）由 gain_table 內插：0.80→0.192、0.93→0.167、1.06→0.159、1.22→0.150、1.37→0.130，實測值 [src: raw/project/snapshot-20261123d/lap_ff.json#key=gain_table] [src: raw/project/snapshot-20261123d/lap_ff.py#L19]。

**arc2.c3 x-band（r2）** [src: raw/project/snapshot-20261123d/lap_ff.py#L606-L638]：
```
prof = c_eff + u_x(x)
raw  = clip(prof + k_e·(near − e_c_x(x)) + k_gz·(gz + v·κ_x) + k_h·(h_x(x) − 已轉) + k_y·(y − y_x(x)),
            中心 − floor_below, 中心 + cap_rel)，速率 ≤ rate_us_s
out  = in + w_x(x)·we·(raw − in)，we = clip((e_max − near)/e_band, 0, 1)
```
k_e 80（±80）、k_h 6（±80）、k_gz 1.0（±40）、k_y 5（±60）、rate 700 µs/s、cap_rel 280、floor_below 40、e_max 1.0、e_band 0.08，皆調參值 [src: raw/project/snapshot-20261123d/arc2.json#L1020-L1033] [src: raw/project/snapshot-20261123d/arc2.json#L1140-L1143]。

**彎 4 帶狀**：結構同彎 1／2，κ_turn 15～30° 約 45～46、61～157° 為 20、193° 為 0；e_c 0.44（另有 e_c_turn 表）；k_e 200；m_hi 120（下限 40）；floor_below 40 [src: raw/project/snapshot-20261123d/lap_ff.json#key=c4.band.kappa_turn] [src: raw/project/snapshot-20261123d/lap_ff.json#key=c4.band.k_e_us] [src: raw/project/snapshot-20261123d/lap_ff.py#L696-L707]。

## 未確認

- arc2.c3.top 的絕對上限表沒有隨共用中心平移；是刻意（以 1600 µs 的實際舵機位置為準）還是遺漏，資料看不出，已列入衝突草稿 [src: raw/project/snapshot-20261123d/arc2.json#L556-L574]。
- curve_map 彎角表 140／195／268° 與專案說明檔「彎1／彎2／彎3＝150°／210°／268°」寫法不同；後者可能是跑道實際彎角而非地圖設定值，已列入衝突草稿 [src: raw/records/logs/AGENTS.md#L7] [src: raw/project/snapshot-20261123d/curve_map.json#L1]。
- 各彎帶狀在最終版的實車效果（內外線淨空、圈速）不在本頁。
- lap_ff 程式說明寫「NOT deployed」[src: raw/project/snapshot-20261123d/lap_ff.py#L1]，與 json 開啟矛盾；依規則以 json＋呼叫為準，說明文字過時。

## 相關條目

- [[control/pid-core]]、[[control/command-chain]]、[[control/yaw-inner]]
- [[control/lap-position]]（觸發用的地標與里程）
- [[control/slope-downhill]]（彎 4 前段由 land4 負責）
- [[control/play-comp]]（輸出端間隙補償）
- [[control/lost-path]]、[[control/disabled-layers]]
- [[hardware/steering-servo]]、[[synthesis/imu-roles]]
