---
id: control/heading-hold
title: 直線與路口的航向保持（多層並存）
status: mixed
sources:
  - raw/project/snapshot-20261123d/live_pid.py
  - raw/project/snapshot-20261123d/cmd_comp.py
  - raw/project/snapshot-20261123d/cmd_comp.json
  - raw/project/snapshot-20261123d/crossing_pass.json
  - raw/project/snapshot-20261123d/xp_anchor.json
  - raw/project/snapshot-20261123d/gyro_hold.py
  - raw/project/snapshot-20261123d/gyro_hold.json
  - raw/project/snapshot-20261123d/arc2.py
  - raw/project/snapshot-20261123d/arc2.json
  - raw/project/snapshot-20261123d/heading_hold.py
  - raw/project/snapshot-20261123d/upper_single.py
  - raw/project/snapshot-20261123d/upper_single.json
  - raw/project/snapshot-20261123d/down_straight.json
  - raw/project/snapshot-20261123d/straight_slew.py
  - raw/project/snapshot-20261123d/straight_slew.json
  - raw/project/snapshot-20261123d/xp_corridor.json
  - raw/project/snapshot-20261123d/crossings_ctl.json
  - raw/project/snapshot-20261123d/yaw_inner.json
  - raw/project/snapshot-20261123d/heading_term.json
  - raw/project/snapshot-20261123d/gyro_damp.json
  - raw/project/snapshot-20261123d/curve_hold.json
verified_against: snapshot-20261123d
updated: 2026-11-23
---

# 直線與路口的航向保持

## 一句話結論

【現役】最終版的「直線鎖定」不是單一策略，而是依路段分給不同層：平地直線用指令在途補償（cmd_comp）＋陀螺儀內迴圈；兩個路口用 lap_pos 位置窗內的「IMU 航向保持」（arc2.blind、arc2.blind_c2）並由 crossing_pass 縮小相機權重；上層虛線轉彎後用 upper_single 單一控制律；陡下坡由 land4 全權（down_straight 的限幅與陀螺儀保持只在 land4 沒有參考或沒有 IMU 時才會送出，見 [[control/slope-downhill]]）；【曾用】另有六種直線類層已在最終版關閉 [src: raw/project/snapshot-20261123d/live_pid.py#L2235-L2292]。

## 內容

名詞：
- 航向（yaw）：IMU 陀螺儀積分出的車頭方向，左轉為正（deg）[src: raw/project/snapshot-20261123d/gyro_hold.py#L5]。
- lap_pos：以編碼器里程加地標（C1e＝彎 1 出口、C2e＝彎 2 出口等）推算的圈內位置，見 [[control/lap-position]]。
- 層表：`live_pid.py` 的 `VALID_LAYERS`，有效格由上往下執行，後寫入舵量者生效 [src: raw/project/snapshot-20261123d/segment_ctx.py#L143-L157]。

### 1.【現役】cmd_comp：平地直線的指令在途補償
- 問題：相機看到修正效果約需 1 s，直線上 PID 會為「已送出、尚未生效」的修正繼續加碼，形成週期 3～6 s、±0.45 的 S 型 [src: raw/project/snapshot-20261123d/cmd_comp.py#L1-L5]。
- 做法：舵量減去 kp·k·Σ(u·dt)（過去 window_s 內實際送出的偏移積分），上限 ±cap_us；只在平地直線（WAIT_CLIMB、|俯仰| ≤ 3°、非地圖彎、|gz| < gz_max）作用 [src: raw/project/snapshot-20261123d/cmd_comp.py#L45-L55] [src: raw/project/snapshot-20261123d/live_pid.py#L1000-L1006]。
- 層表位置：yaw_group 內、crossing_pass 與 yaw_inner 之前 [src: raw/project/snapshot-20261123d/live_pid.py#L2253]。之後由 [[control/yaw-inner]] 再加轉速修正。

### 2.【現役】crossing_pass：圓圈路口窗口的相機縮減
- 窗口錨點：xp_anchor 開啟時，錨點＝lap_pos 判到 C2e 時的 curve_map 里程＋k_m 2.8 m（取代舊的 curve_map「彎 2 結束」事件）[src: raw/project/snapshot-20261123d/live_pid.py#L1011-L1021] [src: raw/project/snapshot-20261123d/xp_anchor.json#key=k_m] [src: raw/project/snapshot-20261123d/xp_anchor.json#key=pos_window]。
- 窗口：錨點後 start_m 0.4 ～ end_m 3.5 m，且非彎道 FLOOR、平地 [src: raw/project/snapshot-20261123d/live_pid.py#L1138-L1140] [src: raw/project/snapshot-20261123d/crossing_pass.json#key=end_m]。換算成 lap_pos 約 C2e+3.2～6.3 m（推算：2.8+0.4、2.8+3.5）。
- 窗口內舵量＝中心＋cam_frac·(相機舵量−中心)，cam_frac 0.6 [src: raw/project/snapshot-20261123d/live_pid.py#L1149] [src: raw/project/snapshot-20261123d/crossing_pass.json#key=cam_frac]；|誤差| ≥ release_err 9.0 才交還（實際等於不放手）[src: raw/project/snapshot-20261123d/live_pid.py#L1146] [src: raw/project/snapshot-20261123d/crossing_pass.json#key=release_err]；出窗後 fade_s 0.5 s 漸回 [src: raw/project/snapshot-20261123d/live_pid.py#L1152-L1156]。
- 窗口內 yaw_inner 修正項限 ±term_cap_us 40 [src: raw/project/snapshot-20261123d/live_pid.py#L1210-L1217]。
- 窗口與漸回期間 proposal 帶有 crossing_pass，curve_ff、lap_ff、arc2 c3、V 字路口 blind 都把它當排除條件 [src: raw/project/snapshot-20261123d/live_pid.py#L1276] [src: raw/project/snapshot-20261123d/live_pid.py#L1384]。
- 遺失格（crossing_hold，屬遺失修飾）：最後有效格在窗口內時，最多 max_s 1.5 s 用陀螺儀保持取代 PID_HOLD 的固定舵量 [src: raw/project/snapshot-20261123d/live_pid.py#L475-L497] [src: raw/project/snapshot-20261123d/crossing_pass.json#key=hold_gyro]，詳見 [[control/lost-path]]。

### 3.【現役】arc2.blind（r2）：V 字路口（彎 1 後斜線）
- 窗口：C1e+4.8～7.5 m，前 0.2 m 漸入、後 0.3 m 漸出；之前的 C1e+0～4.8 m 由相機負責 [src: raw/project/snapshot-20261123d/arc2.json#L256-L261] [src: raw/project/snapshot-20261123d/arc2.json#L287]。
- 參考航向：x0 前最後 0.8 m 的距離加權平均 IMU 航向；若該段擺動（範圍 > 4° 或 |平均 gz| > 12 deg/s）改用最後 0.4 m（範圍 ≤ 2.5°），PRE 參考再以相機橫向斜率修正 ±2.5° 內（cam_ref_m 1.5；LATE 參考不套用）；都不行就不保持 [src: raw/project/snapshot-20261123d/arc2.py#L209-L233] [src: raw/project/snapshot-20261123d/arc2.json#L261-L269]。V 字路口沒有 ref_anchor，所以沒有地圖參考可退 [src: raw/project/snapshot-20261123d/arc2.py#L501-L502]。
- 控制律見下方公式；|航向偏差| > 12° 本窗放手，交回相機 [src: raw/project/snapshot-20261123d/arc2.py#L324-L326] [src: raw/project/snapshot-20261123d/arc2.json#key=blind.r2.max_dev_deg]。
- 層表位置：arc2_flat，在 lap_ff 之後、curve_trim 之前；適用條件與 lap_ff 相同（平地正常路徑、不在 crossing_pass 窗口）[src: raw/project/snapshot-20261123d/live_pid.py#L1384] [src: raw/project/snapshot-20261123d/live_pid.py#L1392-L1399]。
- 遺失格：json 說明寫「不處理遺失格」[src: raw/project/snapshot-20261123d/arc2.json#L287]；程式的遺失掛勾只呼叫 blind_c2 [src: raw/project/snapshot-20261123d/live_pid.py#L2161]，兩者一致。
- 油門不受此層影響（PWM untouched）[src: raw/project/snapshot-20261123d/arc2.py#L169]。

### 4.【現役】arc2.blind_c2（r4）：圓圈路口（彎 2 後直線）
- 窗口：C2e+3.3～5.3 m，漸入 0.2 m、漸出 0.3 m；C2e+0～3.3 m 由相機負責並用來估計參考與相機修正 [src: raw/project/snapshot-20261123d/arc2.json#L1176-L1181] [src: raw/project/snapshot-20261123d/arc2.py#L166-L167]。
- 參考航向：同 V 字路口的 PRE／LATE 規則；不行時退到「地圖參考」＝C1e+4～9 m 斜線平均航向 + ref_off_deg −204.7°；PRE／LATE 與地圖參考差 > 4° 也改用地圖 [src: raw/project/snapshot-20261123d/arc2.py#L170-L173] [src: raw/project/snapshot-20261123d/arc2.json#L1152-L1158]。
- 自有適用條件，不排除 crossing_pass 窗口：有效格上它蓋過 crossing_pass 的縮減結果 [src: raw/project/snapshot-20261123d/live_pid.py#L1400-L1409]。
- 遺失格：窗口已啟動（x ≥ 3.3 m、參考已鎖）時，用同一控制律（不含相機）並以窗口車速外推 lap_pos，最多 lost_age_s 1.0 s [src: raw/project/snapshot-20261123d/arc2.py#L338-L350] [src: raw/project/snapshot-20261123d/live_pid.py#L2161]。
- json 說明寫「offline candidate, NOT deployed」[src: raw/project/snapshot-20261123d/arc2.json#L1175]，但 blind_c2.enabled 與 r4.enabled 都是 true、主程式有呼叫，依規則算現役，說明文字過時 [src: raw/project/snapshot-20261123d/arc2.json#L1150] [src: raw/project/snapshot-20261123d/arc2.json#L1177]。

### 5.【現役】heading_hold 與 upper_single：上層虛線轉彎後
- heading_hold：參考＝虛線轉彎前平均航向 + TURN_DEG 75°，路段窗口（route OPEN）關閉時結束 [src: raw/project/snapshot-20261123d/heading_hold.py#L47] [src: raw/project/snapshot-20261123d/heading_hold.py#L122-L127] [src: raw/project/snapshot-20261123d/heading_hold.py#L175]。模式有 HEADING_ONLY（只用航向）與 FOLLOW_BIAS（跟虛線並加航向偏置）[src: raw/project/snapshot-20261123d/heading_hold.py#L182-L206]。
- upper_single（"one" 單一控制律）在有效格上取代 heading_hold 的舵量；heading_hold 仍持續運算參考、虛線閘門與油門用的誤差 [src: raw/project/snapshot-20261123d/live_pid.py#L889-L890] [src: raw/project/snapshot-20261123d/upper_single.json#key=one.enabled]。
- upper_single_final 層排在 land4 之後，保證其後沒有別層改它的舵量 [src: raw/project/snapshot-20261123d/live_pid.py#L1651-L1655] [src: raw/project/snapshot-20261123d/live_pid.py#L2290]。lane_segment、solid_takeover 只在 upper_single 沒出命令時才跑 [src: raw/project/snapshot-20261123d/live_pid.py#L2246-L2247]。
- 遺失格：先 UPPER_SINGLE_HOLD（upper_single 自己的陀螺儀保持），其次 HEADING_BLIND（heading_hold 的純航向，最多 BLIND_MAX_S 6 s）[src: raw/project/snapshot-20261123d/lost_policy.py#L45-L47]。
- 虛線轉彎本身與上層段細節見 [[path/upper-dash-route]]。

### 6.【現役】down_straight：陡下坡
- 俯仰 ≤ steep_deg −8° 時：有效格舵量限制在中心 ±300 µs；遺失格以陀螺儀保持（downhill 設定 k_gz 4、k_yaw 10、±250 µs）取代保持值 [src: raw/project/snapshot-20261123d/live_pid.py#L426-L463] [src: raw/project/snapshot-20261123d/down_straight.json#L1]。
- 層表中排在下坡各層之後 [src: raw/project/snapshot-20261123d/live_pid.py#L2277]；但坡上 land4 的 slope 段會擁有每一格（有參考時），因此 down_straight 的結果多半只是 land4 的輸入、不會送出，見 [[control/slope-downhill]]。

### 7. 共用的陀螺儀保持原語 gyro_hold
- crossing_hold（路口遺失）與 down_straight 的 GYRO 模式共用同一控制律，參數由各自 json 提供，缺鍵時用 gyro_hold.json 的 crossing／downhill 設定 [src: raw/project/snapshot-20261123d/gyro_hold.py#L3-L14] [src: raw/project/snapshot-20261123d/gyro_hold.json#L1-L5]。
- heading_hold 的 HEADING_ONLY／BLIND／LOST、upper_single、bottom_map 是不同控制律，不走這個原語 [src: raw/project/snapshot-20261123d/gyro_hold.py#L16-L18]。

### 【曾用】已關閉的直線類層（最終版不作用）
- straight_slew：enabled false，舵量限速步驟已從程式移除；但它的 mean_gz_max 12 仍被 weave 旗標（判斷「是否真的在轉」）讀取 [src: raw/project/snapshot-20261123d/straight_slew.json#L1] [src: raw/project/snapshot-20261123d/live_pid.py#L995] [src: raw/project/snapshot-20261123d/live_pid.py#L1218-L1219]。
- heading_term、gyro_damp：enabled false，程式步驟已移除 [src: raw/project/snapshot-20261123d/heading_term.json#L1] [src: raw/project/snapshot-20261123d/gyro_damp.json#L1] [src: raw/project/snapshot-20261123d/live_pid.py#L84]。
- curve_hold（curve_hold.json）：enabled false，程式已移除 [src: raw/project/snapshot-20261123d/curve_hold.json#key=enabled] [src: raw/project/snapshot-20261123d/live_pid.py#L84]。
- xp_corridor：enabled false（與 blind_c2 範圍重疊而關閉）[src: raw/project/snapshot-20261123d/xp_corridor.json#L1]。
- yaw_inner 的 heading_hold 模式：false [src: raw/project/snapshot-20261123d/yaw_inner.json#key=heading_hold]。
- crossings_ctl 的 xp1_hold：null，相關程式已在 cleanup-r1 移除 [src: raw/project/snapshot-20261123d/crossings_ctl.json#key=xp1_hold] [src: raw/project/snapshot-20261123d/live_pid.py#L85-L86]。
- 完整清單見 [[control/disabled-layers]]。

## 公式與參數

**cmd_comp** [src: raw/project/snapshot-20261123d/cmd_comp.py#L53-L54]：
```
comp = clip(−kp·k·Σ(u·dt, 最近 window_s), ±cap_us)；out = steer + comp
```
| 參數 | 值 | 性質 | 來源 |
|---|---|---|---|
| window_s | 1.2 s | 實測值（離線相關性最佳視窗） | [src: raw/project/snapshot-20261123d/cmd_comp.json#L1] [src: raw/project/snapshot-20261123d/cmd_comp.py#L5-L7] |
| k_per_us_s | 0.001 | 實測值（離線擬合；0.002 過補） | [src: raw/project/snapshot-20261123d/cmd_comp.json#L1] [src: raw/project/snapshot-20261123d/cmd_comp.py#L6-L7] |
| cap_us／gz_max／min_frames | 120 µs／15 deg/s／3 | 調參值 | [src: raw/project/snapshot-20261123d/cmd_comp.json#L1] |
| kp | 220（PID 參數，起跑時給） | 調參值 | [src: raw/project/snapshot-20261123d/_extra/start_params.json#key=kp] |

**crossing_pass**：`out = c0 + cam_frac·(steer − c0)` [src: raw/project/snapshot-20261123d/live_pid.py#L1149]
| 參數 | 值 | 性質 | 來源 |
|---|---|---|---|
| start_m／end_m | 0.4／3.5 m（自錨點） | 調參值 | [src: raw/project/snapshot-20261123d/crossing_pass.json#L1] |
| cam_frac | 0.6 | 調參值 | [src: raw/project/snapshot-20261123d/crossing_pass.json#key=cam_frac] |
| release_err／fade_s | 9.0／0.5 s | 調參值 | [src: raw/project/snapshot-20261123d/crossing_pass.json#key=fade_s] |
| jump_de／jump_gap_s／jump_step／jump_step_s | 0.8／0.5 s／0.4／0.3 s | 調參值（跳變後不放手） | [src: raw/project/snapshot-20261123d/crossing_pass.json#L1] |
| term_cap_us | 40 µs | 調參值 | [src: raw/project/snapshot-20261123d/crossing_pass.json#key=term_cap_us] |
| hold_gyro k_gz／k_yaw／lim_us／max_s | 4／10／250 µs／1.5 s | 調參值 | [src: raw/project/snapshot-20261123d/crossing_pass.json#key=hold_gyro] |
| xp_anchor k_m／max_decide_m | 2.8 m／2.0 m | 調參值 | [src: raw/project/snapshot-20261123d/xp_anchor.json#L7-L8] |

**gyro_hold 共用律** [src: raw/project/snapshot-20261123d/gyro_hold.py#L63-L73]：
```
u = clip(k_gz·gz + k_yaw·(yaw − ref), ±lim_us)；out = clip(c0 + u, min_us, max_us)
ref = 第一個遺失格的航向
```

**arc2.blind／blind_c2（r2／r4 共用律）** [src: raw/project/snapshot-20261123d/arc2.py#L268-L288]：
```
trim = clip(k_cam·e_lp, ±trim_us)            e_lp：近處誤差低通（tau_s）
I   += ki·dpsi·dt（只在 HOLD 且 |dpsi| < i_gate_deg、|gz| < i_gate_gz），|I| ≤ i_lim
cmd  = s0 + I + k_psi·(yaw − ref) + k_gz·gz + trim，限 s0 ± lim_us
a    = 漸入／漸出權重；out = st + a·(cmd − st)，每格變化 ≤ max_step_us
```
s0＝straight_us 1513，但 single_centre.json 開啟時在起跑時被改成共用中心（最終版 1445）[src: raw/project/snapshot-20261123d/single_centre.py#L107-L116] [src: raw/project/snapshot-20261123d/single_centre.json#key=enabled] [src: raw/project/snapshot-20261123d/_extra/start_params.json#key=center_us]。

| 參數 | V 字路口 | 圓圈路口 | 性質 |
|---|---|---|---|
| 窗口 x0～x1 | C1e+4.8～7.5 m [src: raw/project/snapshot-20261123d/arc2.json#L257-L259] | C2e+3.3～5.3 m [src: raw/project/snapshot-20261123d/arc2.json#L1178-L1180] | 實測值（路口干擾範圍統計） |
| k_psi／k_gz | 10／1.2 [src: raw/project/snapshot-20261123d/arc2.json#L270-L271] | 12／1.2 [src: raw/project/snapshot-20261123d/arc2.json#L1188-L1189] | 調參值 |
| ki／i_lim | 8／25 µs [src: raw/project/snapshot-20261123d/arc2.json#L272-L273] | 10／25 µs [src: raw/project/snapshot-20261123d/arc2.json#L1190-L1191] | 調參值 |
| lim_us／max_step_us | 150／60 µs [src: raw/project/snapshot-20261123d/arc2.json#L276-L277] | 150／60 µs [src: raw/project/snapshot-20261123d/arc2.json#L1194-L1195] | 調參值 |
| k_cam／trim_us／tau_s | 100／36 µs／0.5 s [src: raw/project/snapshot-20261123d/arc2.json#L278-L280] | 100／36 µs／0.5 s [src: raw/project/snapshot-20261123d/arc2.json#L1196-L1198] | 調參值 |
| max_dev_deg（放手） | 12° [src: raw/project/snapshot-20261123d/arc2.json#L285] | 12° [src: raw/project/snapshot-20261123d/arc2.json#L1203] | 調參值 |
| ref_m／ref_late_m／swing_deg | 0.8 m／0.4 m／4° [src: raw/project/snapshot-20261123d/arc2.json#L261-L263] | 0.8 m／0.4 m／4° [src: raw/project/snapshot-20261123d/arc2.json#L1182-L1184] | 調參值 |
| 地圖參考 | 無 | C1e+4～9 m 平均 −204.7° [src: raw/project/snapshot-20261123d/arc2.json#L1153-L1158] | 實測值（67 次中位數） |

**heading_hold（上層）** [src: raw/project/snapshot-20261123d/heading_hold.py#L182-L206]：
```
FOLLOW_BIAS：out = c + 0.6·(steer − c) − clip(6·err, ±150) + clip(5·gz, ±120)
HEADING_ONLY：out = c − clip(25·err + I, ±360)，I 每秒 4 µs/deg 累積、≤ 120
err = ref − yaw
```
常數 K_HOLD 25、LIM_HOLD 360、CAM_FOLLOW 0.6、K_FOLLOW 6、LIM_FOLLOW 150、K_I_HOLD 4、K_D_DASH 5，皆為程式內調參值 [src: raw/project/snapshot-20261123d/heading_hold.py#L41] [src: raw/project/snapshot-20261123d/heading_hold.py#L45] [src: raw/project/snapshot-20261123d/heading_hold.py#L82-L83]。

**upper_single "one"** [src: raw/project/snapshot-20261123d/upper_single.py#L5-L13]：
```
u = c + I + clip(k_psi·(phi − tgt), ±lim_psi) + clip(k_r·gz, ±lim_r)，再以 slew_us_s 限速
```
k_psi 15、lim_psi 360、k_r 1.0、lim_r 80、ki 4、i_lim 60、slew 1800 µs/s，皆調參值 [src: raw/project/snapshot-20261123d/upper_single.json#key=one.k_psi] [src: raw/project/snapshot-20261123d/upper_single.json#key=one.lim_r] [src: raw/project/snapshot-20261123d/upper_single.json#key=slew_us_s]。

**down_straight**：steep_deg −8、valid_cap_us 300、k_gz 4、k_yaw 10、lim_us 250，皆調參值 [src: raw/project/snapshot-20261123d/down_straight.json#L1]。

## 未確認

- crossing_pass 窗口換成 lap_pos 座標的 C2e+3.2～6.3 m 是由 k_m 與 start_m／end_m 相加推算；錨點用的是 curve_map 里程，兩套里程是否逐格對齊未驗證 [src: raw/project/snapshot-20261123d/live_pid.py#L1020]。
- 專案說明檔描述的路口窗口（彎 2 後 0.4～2.2 m、彎 1 後 3.0～4.6 m）與最終版 json 不符，已列入衝突草稿 [src: raw/records/logs/AGENTS.md#L8]。
- crossing_pass 縮減與 blind_c2 在 C2e+3.3～5.3 m 重疊：有效格由 blind_c2 決定，但其漸入漸出前後各數十公分仍以 crossing_pass 的 0.6 倍相機為輸入；實車在重疊區的貢獻比例未統計。 [src: raw/project/snapshot-20261123d/live_pid.py#L1400-L1409]

## 相關條目

- [[control/yaw-inner]]、[[control/pid-core]]、[[control/command-chain]]
- [[control/lap-position]]（C1e／C2e 地標）
- [[path/junction-handling]]（路口的影像處理側）
- [[path/upper-dash-route]]（上層虛線轉彎）
- [[control/lost-path]]、[[control/slope-downhill]]、[[control/disabled-layers]]
- [[experiments/s-weave]]、[[synthesis/imu-roles]]
