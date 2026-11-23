---
id: control/yaw-inner
title: 陀螺儀內迴圈（yaw_inner）壓住直線 S 型
status: implemented
sources:
  - raw/project/snapshot-20261123d/yaw_inner.py
  - raw/project/snapshot-20261123d/yaw_inner.json
  - raw/project/snapshot-20261123d/live_pid.py
  - raw/project/snapshot-20261123d/segment_ctx.py
  - raw/project/snapshot-20261123d/curve_map.json
  - raw/project/snapshot-20261123d/crossing_pass.json
verified_against: snapshot-20261123d
updated: 2026-11-23
---

# 陀螺儀內迴圈（yaw_inner）

## 一句話結論

相機 PID 算出的舵量先被解讀成「希望車子轉多快」，再用 IMU 陀螺儀量到的實際轉速補差額；這是一個以轉速為目標的內迴圈，在平地、爬坡、坡頂與陡下坡的正常路徑格上作用，用來壓住只靠相機時約 2.3～3.3 s 週期的直線 S 型擺動 [src: raw/project/snapshot-20261123d/yaw_inner.py#L3-L7] [src: raw/project/snapshot-20261123d/yaw_inner.json#key=enabled]。

## 內容

### 為什麼需要它
- 11-07 的分析指出，橫向控制是「誤差 → 舵量 → 轉速 → 航向 → 橫向位置」，中間有兩次積分，總延遲約 0.75 s，其中 0.5～0.6 s 是「命令 → 車子開始轉」[src: raw/project/snapshot-20261123d/yaw_inner.py#L3-L5]。
- 這樣的迴路不論 kp／kd 怎麼調都在穩定邊緣：直線 S 型（週期 2.3～3.3 s、幅度 0.35～0.6）不隨 kp ×0.67、kd 60～200、車速 15～22 或間隙補償改變 [src: raw/project/snapshot-20261123d/yaw_inner.py#L5-L6]。實測與歷史版本的效果見 [[experiments/s-weave]]。
- 做法：把外迴圈命令 u（PID 與增益排程後、相對中心的舵量偏移）解讀成轉速目標 r＝−gain·u，再加一項 k·(r−gz) 的修正。車還沒轉起來時命令會被推大一點；過中心時殘留的轉速（例如 −25 deg/s）立刻被反向抵銷，而不是 0.5 s 後才從相機看到 [src: raw/project/snapshot-20261123d/yaw_inner.py#L10-L15]。
- 名詞：gz＝IMU 量到的偏航角速度（左轉為正，deg/s），由 50 Hz 的 IMU 紀錄檔讀出 [src: raw/project/snapshot-20261123d/yaw_inner.py#L10] [src: raw/project/snapshot-20261123d/gyro_hold.py#L5]。

### 在層表中的位置
- 主控制 `live_pid.py` 每個有效格依 `VALID_LAYERS` 表由上往下執行，後寫入舵量者生效 [src: raw/project/snapshot-20261123d/segment_ctx.py#L143-L157]。
- yaw_inner 屬於 `yaw_group` 群組，順序為 yaw_prelude → curve_map → curve_ctx → cmd_comp → crossing_pass → curve_smooth → arc2_pre → **yaw_inner** → xp_term_cap → weave_flag [src: raw/project/snapshot-20261123d/live_pid.py#L2249-L2259]。整個群組排在 gain_schedule 之後 [src: raw/project/snapshot-20261123d/live_pid.py#L2248]。
- 因此它的輸入「PID 舵量」實際上已經過增益排程、指令在途補償（cmd_comp，見 [[control/heading-hold]]）、圓圈路口的相機縮減（crossing_pass）與彎道低通（curve_smooth）[src: raw/project/snapshot-20261123d/live_pid.py#L2248-L2256]。
- 會蓋過它的後段層：curve_ff、lap_ff、arc2_flat、curve_trim（見 [[control/curve-band-ff]]），下坡與落地各層、land4（見 [[control/slope-downhill]]），以及上層段的 upper_single_final [src: raw/project/snapshot-20261123d/live_pid.py#L2262-L2290]。在急彎帶狀全權區內，yaw_inner 的輸出只是帶狀層的輸入，最後舵量由帶狀層決定（見 [[control/curve-band-ff]]）。
- 圓圈路口窗口內，xp_term_cap 把內迴圈修正項限制在 ±40 µs [src: raw/project/snapshot-20261123d/live_pid.py#L1210-L1217] [src: raw/project/snapshot-20261123d/crossing_pass.json#key=term_cap_us]。

### 適用的格（以程式為準）
- 程式的適用條件 `ely`：理由為 PROPOSAL_ONLY（正常有效 PID 格）、有俯仰值、路段狀態為 WAIT_CLIMB／CLIMBED／OPEN，或為 DONE 但正在陡下坡（俯仰 ≤ −10°）或已回到平地；且不在車道段、航向保持未啟動、不在虛線轉彎、沒有特殊路徑來源；下坡 4 s 尾段內只有陡坡或平地格可用 [src: raw/project/snapshot-20261123d/live_pid.py#L952-L958] [src: raw/project/snapshot-20261123d/segment_ctx.py#L52-L73]。
- 程式說明文字寫「Only on normal flat-path frames」[src: raw/project/snapshot-20261123d/yaw_inner.py#L17]，但 r6 起程式已改成「每個俯仰都進來，由 yaw_inner 自己分平地、爬坡、坡頂、下坡、過渡」[src: raw/project/snapshot-20261123d/live_pid.py#L957-L958]；說明文字過時，以程式為準。
- 模組內再分模式 [src: raw/project/snapshot-20261123d/yaw_inner.py#L64-L79]：
  - 俯仰 ≥ 5°（climb_pitch）：爬坡模式，增益改用 climb_gain [src: raw/project/snapshot-20261123d/yaw_inner.json#key=climb_pitch]。
  - 坡頂保持：俯仰曾 ≥ 8° 且已爬 ≥ 2.0 s，之後 1.0 s 內且俯仰 > −5°，改走 `_crest`（相機命令以 400 µs/s 限速跟隨，內迴圈保持該轉速）[src: raw/project/snapshot-20261123d/yaw_inner.py#L67-L72] [src: raw/project/snapshot-20261123d/yaw_inner.py#L170-L187]。
  - 俯仰 ≤ −10°：下坡模式，增益 downhill_gain，且 down_push false＝只抵抗轉動、不推 [src: raw/project/snapshot-20261123d/yaw_inner.py#L66] [src: raw/project/snapshot-20261123d/yaw_inner.py#L119] [src: raw/project/snapshot-20261123d/yaw_inner.json#key=down_push]。
  - 其餘 |俯仰| > 3° 的格（坡口、坡腳過渡）：TRANSITION，不作用並重設濾波 [src: raw/project/snapshot-20261123d/yaw_inner.py#L76]。
  - 上坡（俯仰 ≥ 5°）結束後 1.0 s 內：CREST_SETTLE，不作用 [src: raw/project/snapshot-20261123d/yaw_inner.py#L74] [src: raw/project/snapshot-20261123d/yaw_inner.py#L77]。
  - 不適用格、無陀螺儀：重設並原樣輸出 [src: raw/project/snapshot-20261123d/yaw_inner.py#L78-L79]。

### 與彎道地圖的配合
- curve_map 不直接出命令，只在「已知彎道尚未轉完」時給內迴圈一個轉速下限：目標轉速不得高於 −20 deg/s（即至少右轉 20 deg/s）[src: raw/project/snapshot-20261123d/yaw_inner.py#L100-L102] [src: raw/project/snapshot-20261123d/curve_map.json#key=floor_dps]。
- 彎 4 出彎後 C4e+0～9 m 內不給此下限（c4_exit）[src: raw/project/snapshot-20261123d/live_pid.py#L969-L972] [src: raw/project/snapshot-20261123d/curve_map.json#key=c4_exit]。
- curve_map 的 lock 模式（用地圖轉速取代下限）在 json 為 false，未使用 [src: raw/project/snapshot-20261123d/curve_map.json#key=lock]，見 [[control/disabled-layers]]。

## 公式與參數

基本式（程式第 103 行）[src: raw/project/snapshot-20261123d/yaw_inner.py#L94-L103]：

```
u      = clip(steer − center, ±max_u_us)
target = −g(v)·u                       （deg/s；地圖下限可把 target 再往右壓）
term   = clip(k·(gz_lp − target), ±cap_us) = clip(k·(g(v)·u + gz_lp), ±cap_us)
out    = clip(steer + term, min_us, max_us)
```

g(v) 依車速線性內插：v ≤ v_lo 用 gain_lo，v ≥ v_hi 用 gain_hi [src: raw/project/snapshot-20261123d/yaw_inner.py#L39-L45]。

| 參數 | 值 | 性質 | 來源 |
|---|---|---|---|
| k_us_per_dps | 4.0 | 調參值（說明文字寫 8 是舊值） | [src: raw/project/snapshot-20261123d/yaw_inner.json#key=k_us_per_dps] |
| speed_gain／v_lo／v_hi | true／0.35／0.55 m/s | 調參值 | [src: raw/project/snapshot-20261123d/yaw_inner.json#L8-L11] |
| gain_lo／gain_hi | 0.047／0.07 deg/s per µs | 實測值（命令→轉速斜率；11-07 合併斜率 0.073）| [src: raw/project/snapshot-20261123d/yaw_inner.json#L10-L12] [src: raw/project/snapshot-20261123d/yaw_inner.py#L7] |
| cap_us | 120 µs | 調參值 | [src: raw/project/snapshot-20261123d/yaw_inner.json#key=cap_us] |
| gz_tau_s | 0.1 s（gz 低通） | 調參值 | [src: raw/project/snapshot-20261123d/yaw_inner.json#key=gz_tau_s] |
| max_u_us | 400 µs | 設計假設（線性範圍） | [src: raw/project/snapshot-20261123d/yaw_inner.json#key=max_u_us] |
| climb_gain／climb_pitch | 0.048／5° | 調參值 | [src: raw/project/snapshot-20261123d/yaw_inner.json#L21-L22] |
| crest_hold_pitch／crest_delay_s／crest_hold_s | 8°／2.0 s／1.0 s | 調參值 | [src: raw/project/snapshot-20261123d/yaw_inner.json#L23-L25] |
| cam_frac／cam_cap_us／cam_rate_us_s | 1.0／400 µs／400 µs/s | 調參值（坡頂模式） | [src: raw/project/snapshot-20261123d/yaw_inner.json#L26-L31] |
| downhill_gain／down_pitch／flat_pitch | 0.048／−10°／3° | 調參值 | [src: raw/project/snapshot-20261123d/yaw_inner.json#L28-L30] |
| settle_pitch／settle_s | 5°／1.0 s | 調參值 | [src: raw/project/snapshot-20261123d/yaw_inner.json#L17-L18] |
| curve_hold／bend_min／u_min／bend_entry | true／10°／60 µs／20° | 調參值 | [src: raw/project/snapshot-20261123d/yaw_inner.json#L13-L16] |
| push_cap／u_straight | 40 µs／450 µs | 調參值 | [src: raw/project/snapshot-20261123d/yaw_inner.json#L19-L20] |
| hold_far | 0.3 | 調參值 | [src: raw/project/snapshot-20261123d/yaw_inner.json#key=hold_far] |
| curve_pull_cap | 40 µs | 調參值 | [src: raw/project/snapshot-20261123d/yaw_inner.json#key=curve_pull_cap] |
| weave_unhold_dps／weave_unhold_s | 20 deg/s／1.5 s | 調參值 | [src: raw/project/snapshot-20261123d/yaw_inner.json#L54-L55] |
| map_done_unhold_margin_deg | 0° | 調參值 | [src: raw/project/snapshot-20261123d/yaw_inner.json#key=map_done_unhold_margin_deg] |
| term_rate_us_s | 600 µs/s | 調參值 | [src: raw/project/snapshot-20261123d/yaw_inner.json#key=term_rate_us_s] |
| oppose_cap_us／oppose_err | 30 µs／0.05 | 調參值 | [src: raw/project/snapshot-20261123d/yaw_inner.json#L59-L60] |
| curve_smooth_tau_s | 0.15 s | 調參值（curve_smooth 層用） | [src: raw/project/snapshot-20261123d/yaw_inner.json#key=curve_smooth_tau_s] |

修正項的各種限制與放手規則（依程式順序）[src: raw/project/snapshot-20261123d/yaw_inner.py#L104-L134]：
- curve_hold：彎內（路徑彎角 ≥ 10°、|u| > 60 µs）車已照命令方向轉時，不反向抵抗；入彎時（|u| ≤ 60 µs 但彎角 ≥ 20°）亦同 [src: raw/project/snapshot-20261123d/yaw_inner.py#L106-L111]。
- weave 模式：平地上 1.5 s 內至少 5 筆 gz、且同時出現 ≥ +20 與 ≤ −20 deg/s（左右擺），或地圖彎已轉完，則取消上述保持、全力阻尼 [src: raw/project/snapshot-20261123d/live_pid.py#L1204-L1207]。
- hold_far：在彎中且遠方列仍朝車轉向延伸（|far| ≥ 0.3），不抵抗 [src: raw/project/snapshot-20261123d/yaw_inner.py#L113-L115]。
- push_cap：直線上（|u| < 450）往命令方向「推」的修正最多 40 µs [src: raw/project/snapshot-20261123d/yaw_inner.py#L117-L118]。
- curve_pull_cap：地圖彎未完成時，往外「拉」的修正最多 40 µs [src: raw/project/snapshot-20261123d/yaw_inner.py#L121-L122]。
- oppose_cap：|相機近處誤差| ≥ 0.05 且修正方向與相機相反時，最多 30 µs [src: raw/project/snapshot-20261123d/yaw_inner.py#L127-L129]。
- term_rate：修正項每秒最多變 600 µs [src: raw/project/snapshot-20261123d/yaw_inner.py#L131-L133]。

內迴圈增益（推算）：k×g＝4×0.047～4×0.07＝0.19～0.28；說明文字中的 8×0.073＝0.58 是 r1 數值 [src: raw/project/snapshot-20261123d/yaw_inner.py#L15-L16] [src: raw/project/snapshot-20261123d/yaw_inner.json#L3-L12]。

## 未確認

- 程式說明寫「閉迴路未驗證」[src: raw/project/snapshot-20261123d/yaw_inner.py#L18]；最終版各參數對 S 型的實際抑制幅度不在本頁，見 [[experiments/s-weave]]。
- json 中 pv_k null（入彎預覽關）、heading_hold false（直線航向保持模式關）、curve_cap_us null 的效果見 [[control/disabled-layers]]；這三項是否在其他版本開啟過，本頁未查。
- gain_dps_per_us 0.073 只在 speed_gain 關或無車速時才用 [src: raw/project/snapshot-20261123d/yaw_inner.py#L41]；最終版實際多數格走車速內插，比例未統計。

## 相關條目

- [[control/pid-core]]（外迴圈相機 PID）
- [[control/command-chain]]（整條舵量命令鏈）
- [[control/heading-hold]]（直線與路口的其他航向層）
- [[control/curve-band-ff]]（彎內會蓋過本層的帶狀前饋）
- [[control/slope-downhill]]（坡道模式的上下游）
- [[hardware/imu-mpu6050]]、[[synthesis/imu-roles]]
- [[experiments/s-weave]]
- [[control/disabled-layers]]
