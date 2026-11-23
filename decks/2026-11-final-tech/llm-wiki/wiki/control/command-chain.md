---
id: control/command-chain
title: 一格命令的計算鏈：層表順序、遺失格、輸出階段
status: mixed
sources:
  - raw/project/snapshot-20261123d/live_pid.py
  - raw/project/snapshot-20261123d/segment_ctx.py
  - raw/project/snapshot-20261123d/lost_policy.py
  - raw/project/snapshot-20261123d/lost_policy.json
  - raw/project/snapshot-20261123d/output_stage.py
  - raw/project/snapshot-20261123d/output_stage.json
  - raw/project/snapshot-20261123d/manual_drive.py
  - raw/project/snapshot-20261123d/gain_schedule.py
  - raw/project/snapshot-20261123d/gain_schedule.json
  - raw/project/snapshot-20261123d/right_entry.py
  - raw/project/snapshot-20261123d/single_centre.py
  - raw/project/snapshot-20261123d/single_centre.json
  - raw/project/snapshot-20261123d/ops07_runtime.py
  - raw/project/snapshot-20261123d/speed_policy.py
  - raw/project/snapshot-20261123d/_extra/start_params.json
  - raw/project/snapshot-20261123d/arc2.json
  - raw/project/snapshot-20261123d/arc_lat.json
  - raw/project/snapshot-20261123d/curve_trim.json
  - raw/project/snapshot-20261123d/xp_corridor.json
  - raw/project/snapshot-20261123d/straight_slew.json
  - raw/project/snapshot-20261123d/yaw_inner.json
  - raw/project/snapshot-20261123d/bottom_guide.json
  - raw/project/snapshot-20261123d/jump_guard.json
  - raw/project/firmware-pwm100_v1/Drive.cpp
  - raw/records/runs/run-b541-20261123/summary.json
verified_against: snapshot-20261123d
updated: 2026-11-23
---

# 一格命令的計算鏈：層表順序、遺失格、輸出階段

## 一句話結論

每收到一格影像，主程式先判斷路徑有效與否：有效格由 PID 算出提案後，依 `VALID_LAYERS` 層表約 50 層依序改寫轉向與油門，遺失格改走 `lost_policy` 的保持表；兩者最後都經同一個輸出階段（間隙補償）交給 manual_drive，再由它以 1500 µs/s 速率限制、夾在 780～2050 µs 後經 UART 送到控制板 [src: raw/project/snapshot-20261123d/live_pid.py#L2151-L2193] [src: raw/project/snapshot-20261123d/manual_drive.py#L387-L403]。

## 內容

### 整體流程（每格）

1. **有效性判斷**：路徑無效，或影像擷取時間距今超過 max_gap（0.4 s）時，走遺失格分支 [src: raw/project/snapshot-20261123d/live_pid.py#L2151-L2153]。
2. **有效格**：呼叫 PID 的 `step_path` 得到提案（PID 細節見 [[control/pid-core]]）；第一格 WARMUP 時沿用最近送出的命令，沒有就回中心、油門 0；其他無效原因直接結束本輪 [src: raw/project/snapshot-20261123d/live_pid.py#L2171-L2180]。
3. **層表**：`segment_ctx.run(VALID_LAYERS, …)` 依序執行層表；每一層有自己的啟用條件（eligibility），在輪到它時才判斷，所以看得到前面各層寫入的值；改到轉向值的最後一層記為本格「擁有者」（owner）[src: raw/project/snapshot-20261123d/live_pid.py#L2183] [src: raw/project/snapshot-20261123d/segment_ctx.py#L143-L157]。
4. **lap_pos 更新在層表之後**：本格的里程位置（`_lap_pos`）在層表跑完、送出之前才更新 [src: raw/project/snapshot-20261123d/live_pid.py#L2190]；因此層表裡讀 lap_pos 的層（lap_ff、lap_speed、brake_zones、arc2、i_ramp 等）讀到的是**上一格**更新的狀態，程式註解也寫明「lap_pos state of its last update」[src: raw/project/snapshot-20261123d/live_pid.py#L1423]。位置估計見 [[control/lap-position]]。
5. **送出**：`_pid_send` → `output_stage.send` [src: raw/project/snapshot-20261123d/live_pid.py#L2193] [src: raw/project/snapshot-20261123d/live_pid.py#L664-L665]。

### 有效格層表 VALID_LAYERS（依執行順序）

**層（layer）**＝一段「讀提案、可能改寫轉向或油門」的程式；**群組（group）**＝一組共用啟用條件與例外處理的層。下表「狀態」依最終版 json 與啟用條件判定：現役＝設定開啟且會在其路段改寫命令；條件式＝常駐但只在特定路段／狀況作用；只記錄＝會執行但不改命令；關＝設定關閉或不會執行。各層的詳細控制律在相關條目，關閉層的整理見 [[control/disabled-layers]]。

| # | 層名 | 作用 | 狀態 | 行號 |
|---|---|---|---|---|
| 1 | jump_filter | 誤差在 ≤5 格內正負跳 ≥0.7 時保持上一個送出命令 | 條件式 | [src: raw/project/snapshot-20261123d/live_pid.py#L2236] [src: raw/project/snapshot-20261123d/live_pid.py#L829-L841] |
| 2 | start_centre | 起跑保持時間內回中心、油門 0 | 現役（只在起跑） | [src: raw/project/snapshot-20261123d/live_pid.py#L2237] [src: raw/project/snapshot-20261123d/live_pid.py#L842-L848] |
| 3 | 群組 steer | 以下第 4～35 列只在非 WARMUP 格執行 | — | [src: raw/project/snapshot-20261123d/live_pid.py#L2238] |
| 4 | imu_boost | 依俯仰做上坡油門提升（速度政策第 1 步） | 現役 | [src: raw/project/snapshot-20261123d/live_pid.py#L2239] [src: raw/project/snapshot-20261123d/live_pid.py#L849-L850] |
| 5 | dash_route | 讀本格的上層虛線路線狀態 | 現役（資料） | [src: raw/project/snapshot-20261123d/live_pid.py#L2240] |
| 6 | crest_marks_arm | 坡頂標記的武裝 | 現役（資料） | [src: raw/project/snapshot-20261123d/live_pid.py#L2241] |
| 7 | dash_turn_end | 虛線轉彎轉滿角度後改成 FOLLOW | 條件式（上層） | [src: raw/project/snapshot-20261123d/live_pid.py#L2242] |
| 8 | dash_turn | 虛線轉彎期間依虛線位置往左轉 | 條件式（上層） | [src: raw/project/snapshot-20261123d/live_pid.py#L2243] |
| 9 | heading_hold | 虛線轉彎後保持車道航向直到下坡 | 條件式（上層） | [src: raw/project/snapshot-20261123d/live_pid.py#L2244] |
| 10 | upper_single | 上層單一擁有者：算出要覆蓋的命令 | 現役（上層） | [src: raw/project/snapshot-20261123d/live_pid.py#L2245] |
| 11 | lane_segment | 沿虛線延伸線轉向 | 條件式（upper_single 未接手時才跑） | [src: raw/project/snapshot-20261123d/live_pid.py#L2246] |
| 12 | solid_takeover | 虛線後相機誤差持續偏一側時接手 | 條件式（同上） | [src: raw/project/snapshot-20261123d/live_pid.py#L2247] |
| 13 | gain_schedule | 依油門縮小轉向偏移（見下節） | 現役 | [src: raw/project/snapshot-20261123d/live_pid.py#L2248] |
| 14 | 群組 yaw_group | 陀螺儀相關層，整組一個例外處理 | — | [src: raw/project/snapshot-20261123d/live_pid.py#L2249] |
| 15 | yaw_prelude | 判斷內迴圈是否適用、讀 gz | 現役 | [src: raw/project/snapshot-20261123d/live_pid.py#L2250] |
| 16 | curve_map | 已知彎道的偏航率下限（含彎 4 出彎 c4_exit） | 現役 | [src: raw/project/snapshot-20261123d/live_pid.py#L2251] |
| 17 | curve_ctx | 本格彎道狀態（供後續層） | 現役（資料） | [src: raw/project/snapshot-20261123d/live_pid.py#L2252] |
| 18 | cmd_comp | 平地直線扣除尚在路上的轉向量 | 現役 | [src: raw/project/snapshot-20261123d/live_pid.py#L2253] |
| 19 | crossing_pass | 彎 2 後路口窗口：降低相機權重 | 條件式（路口窗口） | [src: raw/project/snapshot-20261123d/live_pid.py#L2254] |
| 20 | curve_smooth | 彎內相機命令低通（τ 0.15 s） | 條件式（彎內平地） | [src: raw/project/snapshot-20261123d/live_pid.py#L2255] [src: raw/project/snapshot-20261123d/yaw_inner.json#key=curve_smooth_tau_s] |
| 21 | arc2_pre | 坡上預先右轉 | 關（arc2.json pre.enabled false） | [src: raw/project/snapshot-20261123d/live_pid.py#L2256] [src: raw/project/snapshot-20261123d/arc2.json#key=pre.enabled] |
| 22 | yaw_inner | 陀螺儀偏航率內迴圈 | 現役 | [src: raw/project/snapshot-20261123d/live_pid.py#L2257] |
| 23 | xp_term_cap | 路口窗口內限制內迴圈修正量 | 條件式 | [src: raw/project/snapshot-20261123d/live_pid.py#L2258] |
| 24 | weave_flag | 只計算「直線擺動」旗標 | 只記錄（straight_slew.json 關） | [src: raw/project/snapshot-20261123d/live_pid.py#L2259] [src: raw/project/snapshot-20261123d/straight_slew.json#key=enabled] |
| 25 | xp_corridor | 彎 2 後航向走廊 | 關（json enabled false） | [src: raw/project/snapshot-20261123d/live_pid.py#L2260] [src: raw/project/snapshot-20261123d/xp_corridor.json#key=enabled] |
| 26 | gz_up | 記錄原始 gz 給 upper_path | 現役（資料） | [src: raw/project/snapshot-20261123d/live_pid.py#L2261] |
| 27 | curve_ff | 誤差大時把命令推向彎道下限 | 現役 | [src: raw/project/snapshot-20261123d/live_pid.py#L2262] |
| 28 | lap_ff | 彎 1／2 依位置的帶狀前饋（c3 區塊關閉，彎 3 改由 arc2.c3） | 現役 | [src: raw/project/snapshot-20261123d/live_pid.py#L2263] |
| 29 | arc2_flat | 彎 3 下限、V 字路口與圓圈路口盲直行 | 現役 | [src: raw/project/snapshot-20261123d/live_pid.py#L2264] [src: raw/project/snapshot-20261123d/arc2.json#key=c3.enabled] |
| 30 | curve_trim | 彎 1 往外修 30 µs（彎 3 關） | 現役（只彎 1） | [src: raw/project/snapshot-20261123d/live_pid.py#L2265] [src: raw/project/snapshot-20261123d/curve_trim.json#key=curves] |
| 31 | arc_lat | 依量到的橫向位置修正 | 只記錄（四彎 control 皆 false） | [src: raw/project/snapshot-20261123d/live_pid.py#L2266] [src: raw/project/snapshot-20261123d/arc_lat.json#key=zones] |
| 32 | 群組 speed | 速度政策群組 | — | [src: raw/project/snapshot-20261123d/live_pid.py#L2267] |
| 33 | speed_prelude | speed_adapt 的輸入整理 | 現役 | [src: raw/project/snapshot-20261123d/live_pid.py#L2268] |
| 34 | upper_path | 上層依里程的航向／轉向表 | 現役（上層） | [src: raw/project/snapshot-20261123d/live_pid.py#L2269] |
| 35 | speed_adapt | 依路徑穩定度決定油門等級 | 現役 | [src: raw/project/snapshot-20261123d/live_pid.py#L2270] |
| 36 | speed_caps | lap_speed→lane_cap→brake_zones→upper_cap→speed_guard | 現役 | [src: raw/project/snapshot-20261123d/live_pid.py#L2271] |
| 37 | downhill_dcap | 下坡 D 項限 ±150 | 條件式（下坡尾段） | [src: raw/project/snapshot-20261123d/live_pid.py#L2272] |
| 38 | downhill_speed | 下坡依輪速縮小轉向偏移 | 條件式（下坡） | [src: raw/project/snapshot-20261123d/live_pid.py#L2273] |
| 39 | downhill_assist | 下坡右誤差明確時右轉下限 | 條件式（下坡） | [src: raw/project/snapshot-20261123d/live_pid.py#L2274] |
| 40 | downhill_dlimit | 下坡 D 不得把右修正翻成左 | 條件式（下坡） | [src: raw/project/snapshot-20261123d/live_pid.py#L2275] |
| 41 | downhill_gz | 下坡偏航率限制 | 條件式（下坡） | [src: raw/project/snapshot-20261123d/live_pid.py#L2276] |
| 42 | down_straight | 陡坡段直行保持 | 條件式（下坡） | [src: raw/project/snapshot-20261123d/live_pid.py#L2277] |
| 43 | xp_seen | 路口窗口狀態記帳 | 現役（資料） | [src: raw/project/snapshot-20261123d/live_pid.py#L2278] |
| 44 | downhill_bottom | 坡底單格左跳時保持中位數 | 條件式（bottom_owner 作用時不套用） | [src: raw/project/snapshot-20261123d/live_pid.py#L2279] [src: raw/project/snapshot-20261123d/live_pid.py#L1587] |
| 45 | bottom_left_floor | 坡底不得太左 | 條件式（坡底） | [src: raw/project/snapshot-20261123d/live_pid.py#L2280] |
| 46 | jump_guard | 誤差由右緣單格跳過整條路時保持右舵 | 條件式（min_prev_s 0.2） | [src: raw/project/snapshot-20261123d/live_pid.py#L2281] [src: raw/project/snapshot-20261123d/jump_guard.json#key=min_prev_s] |
| 47 | dh_last_err | 記錄最後有效誤差 | 現役（資料） | [src: raw/project/snapshot-20261123d/live_pid.py#L2282] |
| 48 | wheel | 左右輪差速（已移除，固定空） | 關 | [src: raw/project/snapshot-20261123d/live_pid.py#L2283] [src: raw/project/snapshot-20261123d/live_pid.py#L1640-L1641] |
| 49 | bottom_map_floor | 落地後彎 4 未轉完時的左下限 | 條件式（坡底） | [src: raw/project/snapshot-20261123d/live_pid.py#L2284] |
| 50 | bottom_owner | 落地到彎 4 的右上限與偏航率保持 | 現役（坡底） | [src: raw/project/snapshot-20261123d/live_pid.py#L2285] |
| 51 | lap_ff4 | 彎 4 帶狀前饋 | 現役 | [src: raw/project/snapshot-20261123d/live_pid.py#L2286] |
| 52 | arc2_land | 落地轉彎曲率表 | 現役 | [src: raw/project/snapshot-20261123d/live_pid.py#L2287] [src: raw/project/snapshot-20261123d/arc2.json#key=land.enabled] |
| 53 | bottom_guide | 落地鎖存與距離紀錄 | 只記錄（不改命令） | [src: raw/project/snapshot-20261123d/live_pid.py#L2288] [src: raw/project/snapshot-20261123d/bottom_guide.json#key=enabled] |
| 54 | land4 | 坡上／落地目標航向律 | 現役 | [src: raw/project/snapshot-20261123d/live_pid.py#L2289] |
| 55 | upper_single_final | 上層：把 upper_single 的命令蓋回去 | 現役（上層） | [src: raw/project/snapshot-20261123d/live_pid.py#L2290] |
| 56 | i_ramp | 上坡／出彎釋放積分（只改積分狀態） | 現役 | [src: raw/project/snapshot-20261123d/live_pid.py#L2291] |
| 57 | start_bias | 起步後短暫左偏 −40 µs | 現役（只在起步） | [src: raw/project/snapshot-20261123d/live_pid.py#L2292] |

各控制律：陀螺儀內迴圈見 [[control/yaw-inner]]，上層航向保持見 [[control/heading-hold]]，彎道帶狀前饋見 [[control/curve-band-ff]]，坡道與下坡見 [[control/slope-downhill]]，油門層見 [[control/speed-control]]。

### 遺失格的層序

**遺失格**＝路徑無效或影像過舊的格。它不跑上面的層表，而是查 `LOST_TABLE`（由 lost_policy.json 建立）[src: raw/project/snapshot-20261123d/live_pid.py#L2295]：

1. 依群組順序 blind（UPPER_SINGLE_HOLD→LANE_BLIND_HOLD→HEADING_BLIND）→ pid_hold（PID_HOLD，沿用最後有效命令最多 0.4 s）→ downhill（DOWNHILL_HOLD）→ lost（LOST_HEADING／LOST_TURN），第一個提出命令的列勝出 [src: raw/project/snapshot-20261123d/lost_policy.py#L6-L13] [src: raw/project/snapshot-20261123d/lost_policy.json#key=groups]。
2. 都沒有提出 → 結束本輪（PID_INVALID_OR_STALE_PATH）[src: raw/project/snapshot-20261123d/live_pid.py#L2156-L2157]。
3. 該列的修飾器依序執行（hold_pwm、turn_pwm、down_straight 等），之後再依序讓 lap_ff（彎 2 帶狀）、lap_ff4、arc2 blind_c2、bottom_owner、bottom_guide、arc2 land、land4 改寫遺失格命令 [src: raw/project/snapshot-20261123d/live_pid.py#L2158-L2165]。
4. 送出時同樣經輸出階段（遺失格屬「保持型」，會做間隙補償）[src: raw/project/snapshot-20261123d/live_pid.py#L2167]。

遺失格的分類與失效情境見 [[control/lost-path]] 與 [[path/vision-failure-modes]]。

### gain_schedule：依油門縮小轉向

- 當 speed_adapt 的目前油門高於 ref_pwm 時，轉向偏移乘上 k＝max(k_min, ref_pwm／PWM)；最終版 ref_pwm 19.6、k_min 0.57 [src: raw/project/snapshot-20261123d/gain_schedule.py#L24-L29] [src: raw/project/snapshot-20261123d/gain_schedule.json]。
- 以下情況**不套用**：路徑來源為 dash_route 或 crest_midpoint、heading_hold 作用中、虛線轉彎、下坡視窗、imu_boost 上坡模式 [src: raw/project/snapshot-20261123d/live_pid.py#L934-L949]。
- 右轉偏移超過 +240 µs 時，`right_entry` 逐步取消縮小 [src: raw/project/snapshot-20261123d/right_entry.py#L11-L16]。
- 讀的是上一格的 speed_adapt 油門（speed_policy 的隱藏寫入說明）[src: raw/project/snapshot-20261123d/speed_policy.py#L21]。
- 說明文字記載 11-06 使用者認為舊版縮放反而讓直線擺動變大，常數因此改由 json 設定 [src: raw/project/snapshot-20261123d/gain_schedule.py#L1-L7]；最終版 json 開啟，以 json 為準算現役。

### single_centre：起跑時改寫絕對值

`single_centre.json` 開啟 [src: raw/project/snapshot-20261123d/single_centre.json#key=enabled]。每輪起跑時，lap_ff、arc2、bottom_guide 中代表「直行點」的數值改成共用中心（1445），絕對上限改成「中心＋（原值−1480）」，舵機機械限位 780／2050 不動 [src: raw/project/snapshot-20261123d/single_centre.py#L6-L15] [src: raw/project/snapshot-20261123d/live_pid.py#L590]。檔頭寫「NOT deployed」已過時。

### 輸出階段 output_stage.send

依序 [src: raw/project/snapshot-20261123d/output_stage.py#L103-L117]：

1. **ops07 中心保持**：只在 `orin_continuous` 模式且 ops07 保持中才把命令換成中心、油門 0 [src: raw/project/snapshot-20261123d/ops07_runtime.py#L35-L36]；最終實跑為 `orin_timed` 模式，此步不作用 [src: raw/records/runs/run-b541-20261123/summary.json#L36]。
2. **cmd_comp.sent**：把「補償前」的轉向偏移記入 cmd_comp 的在途命令總和 [src: raw/project/snapshot-20261123d/output_stage.py#L111-L113]。
3. **play_comp**：轉向間隙補償，並夾在 min_us～max_us（見 [[control/play-comp]]）；起跑回中與中心 WARMUP 格不補償 [src: raw/project/snapshot-20261123d/live_pid.py#L658-L661]。output_unify 沒有設定檔，走原路徑 [src: raw/project/snapshot-20261123d/output_stage.py#L60-L71]。
4. **manual.pid_input**：檢查序號遞增、目標在限位內、油門不超過本輪起跑上限，且距上一筆輸入不超過 1 s [src: raw/project/snapshot-20261123d/manual_drive.py#L166-L184]。

### manual_drive：最後的速率限制與夾限

送 UART 的迴圈中，PID 模式的轉向以 `step＝steer_rate_us_s×elapsed`（本輪 1500 µs/s）逐步逼近目標，再夾在限位內，四捨五入成整數脈寬送出 [src: raw/project/snapshot-20261123d/manual_drive.py#L387-L403] [src: raw/records/runs/run-b541-20261123/summary.json#L12]。暫停或 ops07 保持時目標改為中心、油門 0 [src: raw/project/snapshot-20261123d/manual_drive.py#L391-L392]。控制板韌體再以每 20 ms 最多 40 µs（2000 µs/s）追蹤目標 [src: raw/project/firmware-pwm100_v1/Drive.cpp#L314-L321]。輸出階段本身不限速 [src: raw/project/snapshot-20261123d/output_stage.py#L10-L11]。UART 格式見 [[comms/uart-protocol]]。

## 公式與參數

```
gain_schedule:  k = max(0.57, 19.6 / PWM)   （PWM > 19.6 才套用；PWM ≤ 19.6 時 k = 1）
                steer = c + (steer − c) × k
manual_drive:   offset ← offset + clamp(target − c − offset, −rate·Δt, +rate·Δt)
                pulse  = round( c + clamp(offset, min−c, max−c) )
韌體:           steeringUs ← steeringUs + clamp(target − steeringUs, −40, +40)   每 20 ms
```

| 參數 | 值 | 性質 | 出處 |
|---|---|---|---|
| gain_schedule ref_pwm／k_min | 19.6／0.57 | 調參值 | [src: raw/project/snapshot-20261123d/gain_schedule.json] |
| k 到達下限的油門 | 推算 19.6÷0.57≈34.4 | 推算 | [src: raw/project/snapshot-20261123d/gain_schedule.py#L29] |
| right_entry 起點 | +240 µs | 調參值 | [src: raw/project/snapshot-20261123d/right_entry.py#L16] |
| max_gap（遺失判定） | 0.4 s | 設計假設 | [src: raw/project/snapshot-20261123d/_extra/start_params.json#L44] |
| PID_HOLD 保持時間 | 0.4 s | 設計假設 | [src: raw/project/snapshot-20261123d/lost_policy.py#L10] |
| lost_turn_us／downhill_hold_max_s | 200 µs／3.0 s | 調參值 | [src: raw/project/snapshot-20261123d/lost_policy.json#key=lost_turn_us] [src: raw/project/snapshot-20261123d/lost_policy.json#key=downhill_hold_max_s] |
| manual_drive 轉向速率 | 1500 µs/s | 調參值 | [src: raw/records/runs/run-b541-20261123/summary.json#L12] |
| 韌體轉向速率 | 40 µs／20 ms＝2000 µs/s | 調參值 | [src: raw/project/firmware-pwm100_v1/Drive.cpp#L317] |
| pid_input 輸入中斷上限 | 1 s | 設計假設 | [src: raw/project/snapshot-20261123d/manual_drive.py#L170] |
| single_centre 設計中心 | 1480 µs | 設計假設 | [src: raw/project/snapshot-20261123d/single_centre.py#L30] |

## 未確認

- 層表的「狀態」欄以 json 開關與啟用條件判定，未逐格統計 run-b541 中每層實際改寫命令的次數 [src: raw/records/runs/run-b541-20261123/summary.json]；某些「條件式」層在最終版是否真的觸發過，需以逐格紀錄的 owner 欄位另行確認。
- 程式內約有 19 種丟線／壞路徑行為（lost_policy 的 CATALOGUE），本頁只列遺失格表的四組 [src: raw/project/snapshot-20261123d/lost_policy.py#L22-L24]。
- PID、manual_drive、韌體三層速率限制在高速急彎時哪一層實際綁住輸出，未量測。

## 相關條目

- [[control/pid-core]]
- [[control/speed-control]]
- [[control/lap-position]]
- [[control/play-comp]]
- [[control/yaw-inner]]
- [[control/heading-hold]]
- [[control/curve-band-ff]]
- [[control/slope-downhill]]
- [[control/lost-path]]
- [[control/disabled-layers]]
- [[comms/uart-protocol]]
- [[comms/timing-latency]]
- [[overview]]
