---
id: control/lost-path
title: 路徑遺失時的處理（遺失表與各段專屬保持）
status: implemented
sources:
  - raw/project/snapshot-20261123d/live_pid.py
  - raw/project/snapshot-20261123d/lost_policy.py
  - raw/project/snapshot-20261123d/lost_policy.json
  - raw/project/snapshot-20261123d/pid_hold.py
  - raw/project/snapshot-20261123d/heading_hold.py
  - raw/project/snapshot-20261123d/gyro_hold.py
  - raw/project/snapshot-20261123d/crossing_pass.json
  - raw/project/snapshot-20261123d/down_straight.json
  - raw/project/snapshot-20261123d/downhill_speed.py
  - raw/project/snapshot-20261123d/bottom_owner.py
  - raw/project/snapshot-20261123d/bottom_owner.json
  - raw/project/snapshot-20261123d/bottom_guide.py
  - raw/project/snapshot-20261123d/bottom_guide.json
  - raw/project/snapshot-20261123d/bottom_map.json
  - raw/project/snapshot-20261123d/lap_ff.py
  - raw/project/snapshot-20261123d/lap_ff.json
  - raw/project/snapshot-20261123d/arc2.py
  - raw/project/snapshot-20261123d/arc2.json
  - raw/project/snapshot-20261123d/land4.py
  - raw/project/snapshot-20261123d/crest_latch.py
  - raw/project/snapshot-20261123d/stuck_stop.py
  - raw/project/snapshot-20261123d/stuck_stop.json
  - raw/project/snapshot-20261123d/_extra/start_params.json
verified_against: snapshot-20261123d
updated: 2026-11-23
---

# 路徑遺失時

## 一句話結論

相機路徑無效（或影格過舊）時，主程式依 lost_policy.json 的表格依序嘗試「上層陀螺儀保持 → 0.4 s 保持上次命令 → 下坡保持 → 保持最後航向／最後大轉向」，再套各段專屬的陀螺儀或航向表保持；全部不適用或影格過舊就停車（PID_INVALID_OR_STALE_PATH）[src: raw/project/snapshot-20261123d/lost_policy.py#L6-L14] [src: raw/project/snapshot-20261123d/live_pid.py#L2151-L2157]。

## 內容

### 何時算「遺失」
- 有效格＝工作程序回報 valid、算得出誤差、且擷取到處理不超過 0.5 s [src: raw/project/snapshot-20261123d/live_pid.py#L2100]。
- 進入遺失分支：本格無效，或影格年齡 > max_gap 0.4 s [src: raw/project/snapshot-20261123d/live_pid.py#L2151] [src: raw/project/snapshot-20261123d/_extra/start_params.json#key=max_gap]。
- 影格過舊（stale）時四個群組的前置條件都不成立 → 直接停車；安全檢查也會以 PID_VISION_STALE 結束輪次 [src: raw/project/snapshot-20261123d/live_pid.py#L744-L745] [src: raw/project/snapshot-20261123d/live_pid.py#L759-L765] [src: raw/project/snapshot-20261123d/live_pid.py#L779-L781] [src: raw/project/snapshot-20261123d/live_pid.py#L729]。
- 有些有效格會被刻意改成遺失格，交給本頁規則處理：坡頂 crest_latch 鎖住後中點不可用 [src: raw/project/snapshot-20261123d/crest_latch.py#L14-L16]；落地範圍內往左捲的單左線（bottom_guide curl）、航向落後太多（lag_lost）[src: raw/project/snapshot-20261123d/live_pid.py#L2066-L2067]。

### 選列順序（lost_policy.json）
群組依序測試前置條件，第一個提出命令的列勝出 [src: raw/project/snapshot-20261123d/lost_policy.py#L131-L147] [src: raw/project/snapshot-20261123d/lost_policy.json#L3-L30]：

| 順序 | 群組／列 | 條件 | 行為 | 來源 |
|---|---|---|---|---|
| 1 | blind／UPPER_SINGLE_HOLD | 新鮮格、上層 upper_single 已啟動 | upper_single 的陀螺儀保持 | [src: raw/project/snapshot-20261123d/live_pid.py#L748-L749] [src: raw/project/snapshot-20261123d/lost_policy.py#L45] |
| 2 | blind／LANE_BLIND_HOLD | 坡口剛有車道段命令 | 保持車道命令平均 | [src: raw/project/snapshot-20261123d/live_pid.py#L750-L751] [src: raw/project/snapshot-20261123d/lost_policy.py#L46] |
| 3 | blind／HEADING_BLIND | route OPEN、非轉彎、航向參考已設，最後有效格 ≤ 6 s | heading_hold 純航向：中心 − clip(25·err, ±360) | [src: raw/project/snapshot-20261123d/heading_hold.py#L149-L156] [src: raw/project/snapshot-20261123d/heading_hold.py#L33] |
| 4 | pid_hold／PID_HOLD | 新鮮格，最後有效命令 ≤ HOLD_S 0.4 s | 保持最後有效命令 | [src: raw/project/snapshot-20261123d/pid_hold.py#L17] [src: raw/project/snapshot-20261123d/pid_hold.py#L56-L60] |
| 5 | downhill／DOWNHILL_HOLD | 下坡 4 s 尾段內、最後有效格 ≤ 3.0 s | 最近 0.5 s 送出值中位數，限中心 −150～+150（平地坡底 +300；最後誤差明顯向右時放寬到舵機極限） | [src: raw/project/snapshot-20261123d/live_pid.py#L763-L778] [src: raw/project/snapshot-20261123d/lost_policy.json#L72-L73] |
| 6 | lost／LOST_HEADING | 新鮮格、0.4 s 保持已過，最後有效格 ≤ LOST_MAX_S 3 s | 保持最後有效格的航向：中心 − clip(25·err, ±200) | [src: raw/project/snapshot-20261123d/heading_hold.py#L158-L165] [src: raw/project/snapshot-20261123d/heading_hold.py#L65] |
| 6' | lost／LOST_TURN | 同上，但最後命令離中心 ≥ 200 µs 且不在圓圈路口窗口 | 保持最後命令（彎中遺失不回直） | [src: raw/project/snapshot-20261123d/live_pid.py#L785-L790] [src: raw/project/snapshot-20261123d/lost_policy.json#key=lost_turn_us] |
| — | 停車 | 以上都沒有提出 | PID_INVALID_OR_STALE_PATH | [src: raw/project/snapshot-20261123d/live_pid.py#L2157] |

- blind 群組有 catch：任一列出錯時吞掉例外、繼續下一群組 [src: raw/project/snapshot-20261123d/lost_policy.py#L135-L141]。
- LOST_HEADING 的航向參考 track 在每個有效格更新（heading_hold.step 一定執行）[src: raw/project/snapshot-20261123d/heading_hold.py#L170]。

### 各列的修飾（mods）
選定列後依序套用修飾 [src: raw/project/snapshot-20261123d/lost_policy.py#L150-L158] [src: raw/project/snapshot-20261123d/lost_policy.json#L31-L70]：
- hold_pwm／turn_pwm：油門（速度層的保持油門與上層轉彎油門），見 [[control/speed-control]] [src: raw/project/snapshot-20261123d/live_pid.py#L795-L798]。
- down_straight（陡坡 ≤ −8°）：以陀螺儀保持取代保持值，k_gz 4、k_yaw 10、±250 µs [src: raw/project/snapshot-20261123d/live_pid.py#L457-L462] [src: raw/project/snapshot-20261123d/down_straight.json#L1]。
- crossing_hold（圓圈路口）：最後有效格在 crossing_pass 窗口內時，最多 1.5 s 用陀螺儀保持；已有 down_straight GYRO 時讓它優先 [src: raw/project/snapshot-20261123d/live_pid.py#L475-L497] [src: raw/project/snapshot-20261123d/crossing_pass.json#key=hold_gyro]。
- PID_HOLD 另有 downhill_clamp（下坡時限中心 ±150）與 downhill_gz（轉速限制）[src: raw/project/snapshot-20261123d/live_pid.py#L812-L821] [src: raw/project/snapshot-20261123d/downhill_speed.py#L21]。
- DOWNHILL_HOLD 另有 bottom_map（坡底已開始右轉 15～130° 時以轉速目標 30 deg/s 續轉，PWM 15）；bottom_owner 範圍內此項略過 [src: raw/project/snapshot-20261123d/live_pid.py#L803-L809] [src: raw/project/snapshot-20261123d/live_pid.py#L406-L417] [src: raw/project/snapshot-20261123d/bottom_map.json#key=target_dps]。
- 陀螺儀保持共用律見 [[control/heading-hold]] 第 7 節 [src: raw/project/snapshot-20261123d/gyro_hold.py#L63-L73]。

### 各段專屬的遺失處理（修飾之後依序套用）[src: raw/project/snapshot-20261123d/live_pid.py#L2159-L2165]
1. 彎 1／彎 2 帶狀（lap_ff）：帶狀未結束時，最多 lost_max_s 1.0 s 用 profile＋陀螺儀項（不含相機），夾在中心～cap [src: raw/project/snapshot-20261123d/lap_ff.py#L285-L308] [src: raw/project/snapshot-20261123d/lap_ff.json#key=curves.c2.band.lost_max_s]。
2. 彎 4 帶狀（lap_ff4）：x ≥ 1.2 m 且未到結束角，最多 1.0 s，同樣結構 [src: raw/project/snapshot-20261123d/lap_ff.py#L722-L740] [src: raw/project/snapshot-20261123d/lap_ff.json#key=c4.band.lost_max_s]。
3. 圓圈路口 blind_c2：窗口已啟動時用同一航向律（不含相機），lap_pos 以窗口車速外推最多 1.0 s；V 字路口 blind 沒有遺失掛勾 [src: raw/project/snapshot-20261123d/arc2.py#L338-L350] [src: raw/project/snapshot-20261123d/live_pid.py#L2161]。
4. bottom_owner（落地～彎 4 FLOOR）：陀螺儀轉速保持 RATE_HOLD，target −20 deg/s（左轉量 > −55° 前），cmd＝中心＋150＋4·(gz − target)，偏移 ±250，單段遺失最多 2.0 s [src: raw/project/snapshot-20261123d/bottom_owner.py#L20-L23] [src: raw/project/snapshot-20261123d/bottom_owner.json#L1] [src: raw/project/snapshot-20261123d/live_pid.py#L1686-L1697]。
5. bottom_guide：在 RATE_HOLD 會作用的格，改用「落地後距離 s → 目標航向」表保持（s ≤ 4.5 m），cmd＝中心＋ff＋8·(psi − psi_ref(s))＋2·(gz − ω_ref)，限 −100～+350 [src: raw/project/snapshot-20261123d/bottom_guide.py#L6-L23] [src: raw/project/snapshot-20261123d/bottom_guide.json#key=k_psi_us_per_deg] [src: raw/project/snapshot-20261123d/live_pid.py#L1726-L1741]。
6. arc2.land approach：下坡口窗口內的遺失格維持送出值下限，最多 max_s 0.6 s [src: raw/project/snapshot-20261123d/arc2.py#L789-L795] [src: raw/project/snapshot-20261123d/arc2.json#L230-L233]。
7. land4：下坡與落地 0～1.5 m 內，用同一航向律（不含相機項）；它是最後一個遺失掛勾，因此坡上與落地初段的遺失格最終由 land4 決定 [src: raw/project/snapshot-20261123d/live_pid.py#L1485-L1492] [src: raw/project/snapshot-20261123d/land4.py#L207-L210]。

### 最後的停車條件
- 表格沒有任何列提出命令 → PID_INVALID_OR_STALE_PATH [src: raw/project/snapshot-20261123d/live_pid.py#L2157]。
- 影格年齡 > 0.4 s → PID_VISION_STALE（安全檢查）[src: raw/project/snapshot-20261123d/live_pid.py#L729]。
- stuck_stop（mode stop）：馬達在出力（≥ 12%）但兩輪轉速都低於表值 15%、持續 1.0 s → 結束輪次；有效格與遺失格送出前都檢查 [src: raw/project/snapshot-20261123d/stuck_stop.py#L1-L15] [src: raw/project/snapshot-20261123d/stuck_stop.json#L4-L8] [src: raw/project/snapshot-20261123d/live_pid.py#L2166] [src: raw/project/snapshot-20261123d/live_pid.py#L667-L675]。stuck_stop.json 的 note 寫「LOG mode … never stops」，但 mode 鍵是 stop，程式以 mode 為準，note 過時 [src: raw/project/snapshot-20261123d/stuck_stop.json#L3-L5]。
- 遺失後第一個有效格若 PID 回報 WARMUP，改送最近送出的命令（pid-hold-r2）[src: raw/project/snapshot-20261123d/live_pid.py#L2176-L2179]。

## 公式與參數

| 參數 | 值 | 性質 | 來源 |
|---|---|---|---|
| max_gap | 0.4 s | 設計假設（影格最大年齡） | [src: raw/project/snapshot-20261123d/_extra/start_params.json#key=max_gap] |
| HOLD_S（PID_HOLD） | 0.4 s | 設計假設（沿用影格年齡上限） | [src: raw/project/snapshot-20261123d/pid_hold.py#L13-L17] |
| BLIND_MAX_S（HEADING_BLIND） | 6 s | 調參值 | [src: raw/project/snapshot-20261123d/heading_hold.py#L33] |
| LOST_MAX_S／LIM_LOST | 3 s／200 µs | 調參值 | [src: raw/project/snapshot-20261123d/heading_hold.py#L65] |
| K_HOLD | 25 µs/deg | 調參值 | [src: raw/project/snapshot-20261123d/heading_hold.py#L82] |
| lost_turn_us | 200 µs | 調參值 | [src: raw/project/snapshot-20261123d/lost_policy.json#L71] |
| downhill_hold_max_s／downhill_hold_left_us | 3.0 s／150 µs | 調參值 | [src: raw/project/snapshot-20261123d/lost_policy.json#L72-L73] |
| crossing hold_gyro | k_gz 4、k_yaw 10、±250 µs、1.5 s | 調參值 | [src: raw/project/snapshot-20261123d/crossing_pass.json#key=hold_gyro] |
| bottom_owner 遺失 | target −20 deg/s、ff 150、k 4、±250、2.0 s | 調參值 | [src: raw/project/snapshot-20261123d/bottom_owner.json#L1] |
| bottom_guide | k_psi 8、k_gz 2、−100～+350、s_max 4.5 m | 調參值（航向表為 32 次落地中位數，實測值） | [src: raw/project/snapshot-20261123d/bottom_guide.json#key=s_max_m] [src: raw/project/snapshot-20261123d/bottom_guide.py#L9-L13] |
| lap_ff／lap_ff4 帶狀遺失 | 1.0 s | 調參值 | [src: raw/project/snapshot-20261123d/lap_ff.json#key=c4.band.lost_hold] |

LOST_HEADING：`out = clip(中心 − clip(25·(ψ_last − ψ), ±200), min_us, max_us)` [src: raw/project/snapshot-20261123d/heading_hold.py#L163]。

## 未確認

- bottom_guide 的 straight_offset_us 33 會被 single_centre 改成 0 [src: raw/project/snapshot-20261123d/bottom_guide.json#key=straight_offset_us]；實際各段遺失保持在最終版的觸發頻率未統計。
- lost_policy.py 目錄共列 19 種遺失／壞路徑行為，本頁只寫控制側；路徑側（dash_route HOLD_LAST、crest_fallback 等）見 [[path/vision-failure-modes]] [src: raw/project/snapshot-20261123d/lost_policy.py#L43-L64]。

## 相關條目

- [[control/command-chain]]、[[control/pid-core]]
- [[control/heading-hold]]（gyro_hold 共用律、路口與上層保持）
- [[control/curve-band-ff]]、[[control/slope-downhill]]
- [[control/speed-control]]（保持格的油門）
- [[path/vision-failure-modes]]、[[path/junction-handling]]
- [[hardware/imu-mpu6050]]
