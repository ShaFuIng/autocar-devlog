---
id: path/vision-failure-modes
title: 相機失去可靠判斷的情境與有效路徑旗標
status: implemented
sources:
  - raw/project/snapshot-20261123d/live_pid.py
  - raw/project/snapshot-20261123d/_extra/start_params.json
  - raw/project/snapshot-20261123d/junction_live.py
  - raw/project/snapshot-20261123d/offscreen_center.py
  - raw/project/snapshot-20261123d/camera_pair.py
  - raw/project/snapshot-20261123d/crest_fallback.py
  - raw/project/snapshot-20261123d/crossings_worker.json
  - raw/project/snapshot-20261123d/dash_route.py
  - raw/records/logs/AGENTS.md
  - raw/records/logs/AGENTS_HISTORY_until_20261119.md
  - raw/records/runs/run-b541-20261123/summary.json
verified_against: snapshot-20261123d
updated: 2026-11-23
---

# 相機失去可靠判斷的情境與有效路徑旗標

## 一句話結論

相機在這些地方容易看不清或看錯：車頭正前方 27～30 cm 以內完全看不到、彎 1～3 幾乎只看得到外側線、平面交叉路口、虛線轉彎後虛線離開畫面、坡頂與坡口／落地 [src: raw/records/logs/AGENTS.md#L112] [src: raw/records/logs/AGENTS.md#L181]。每一格路徑都帶一個「有效」旗標，經過 worker（基準→路口切換）與控制端（虛線、坡頂覆寫）兩層決定；最後仍無效、或最新影格超過 max_gap 0.4 s，就交給失線規則（[[control/lost-path]]）[src: raw/project/snapshot-20261123d/live_pid.py#L2151-L2160] [src: raw/project/snapshot-20261123d/_extra/start_params.json#key=start.parameters.max_gap]。最終實跑 run-b541 共 2804 格中，控制端最後無效只有 8 格（0.3%），worker 選定無效 73 格（2.6%）集中在高架上層 [src: raw/records/runs/run-b541-20261123/summary.json]。

## 內容

### 情境一：看不到的近處與單側線

- 最近可見地面在前輪最前緣前約 27～30 cm，該列橫向只見約 −21～+18 cm；彎 1～3 幾乎只見外側（左）線 [src: raw/records/logs/AGENTS.md#L112]。27 cm 是「從前輪輪胎最前緣沿地面往前量」，不是鏡頭中心投影 [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L346]。
- 後果：彎道中多半只能「看到一條線＋用寬度比例推中心」（來源 left+width／right+width），中心位置依賴寬度記憶是否正確，見 [[path/mask-to-path]]。

### 情境二：路口與交叉線

- 交叉、岔開的白線可能讓左右配對失敗（CROSSING、DIVERGING_PROFILE）或出現多組合格配對而身分不明 [src: raw/project/snapshot-20261123d/camera_pair.py#L58] [src: raw/project/snapshot-20261123d/offscreen_center.py#L36-L44]。身分不明時整格作廢（AMBIGUOUS_BOUNDARY_IDENTITY），沒有本格邊界時也作廢（NO_CURRENT_BOUNDARY），「不用舊路徑補」[src: raw/project/snapshot-20261123d/offscreen_center.py#L68-L71]。
- 這時透視走廊可接手；走廊的預測路徑只顯示、不可控制（JUNCTION_PREDICTION_NOT_CONTROL），沒有目標則記為 JUNCTION_NO_TARGET [src: raw/project/snapshot-20261123d/junction_live.py#L8-L13] [src: raw/project/snapshot-20261123d/junction_live.py#L219-L222]。詳見 [[path/junction-handling]]。

### 情境三：虛線離開畫面（高架上層）

- 虛線轉彎完成、虛線離開畫面後，近處沒有白線，路徑無效；11-22 統計上層 DASHe+1.3～2.3 m 共 37 次、屬常態，原先被誤記為「0.43 s 沒影格」，已更正 [src: raw/records/logs/AGENTS.md#L181]。
- 上層 worker 端常找不到目標，最終版由 dash_route 以虛線本身的路徑覆寫（selected_source＝dash_route，valid 設為 true）[src: raw/project/snapshot-20261123d/live_pid.py#L1982]，詳見 [[path/upper-dash-route]]。

### 情境四：坡頂（crest）

- 坡頂時車身仰約 14°、前方路面卻是平的：看到的路面地平線下移約 140 px，走廊與固定寬度幾何的配對都會失去它，雖然兩條白線其實都在遮罩裡 [src: raw/project/snapshot-20261123d/crest_fallback.py#L3-L7]。
- 備援 crest-fallback-r3：路徑無效且 IMU 顯示車頭仰起 ≥ 8°（或 2 s 內曾仰起）時，從遮罩底部逐列追兩條白線取中點當路徑，最多連續用 3 s [src: raw/project/snapshot-20261123d/crest_fallback.py#L9-L14] [src: raw/project/snapshot-20261123d/crest_fallback.py#L23-L24]；控制端在路徑無效時嘗試它，成功就標 selected_source＝crest_midpoint [src: raw/project/snapshot-20261123d/live_pid.py#L1985-L1997]。

### 情境五：坡口與落地

- 下坡時 worker 的單線寬度比改用坡上看到的雙線比例（slope_width，pitch ≤ −8°）；坡上校正的走廊（地平線偏低）拒收 [src: raw/project/snapshot-20261123d/crossings_worker.json#key=slope_width] [src: raw/project/snapshot-20261123d/crossings_worker.json#key=corridor_cal_gate]。
- 已知問題：坡上／落地處路徑偶有約 0.5 s 中斷 [src: raw/records/logs/AGENTS.md#L373]；落地前後的控制處理見 [[control/slope-downhill]]。

### 情境六：光線

自動曝光時隧道口左車道線近處大半沒被辨識；改成固定手動 30 ms＋gamma 300 後兩線完整 [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L546]。見 [[perception/camera-capture]]。

### 有效旗標的三層

| 層 | 判定者 | 常見無效原因 | 依據 |
|---|---|---|---|
| A 基準線 | camera-pair-v2 基準估計 | NO_CURRENT_BOUNDARY、AMBIGUOUS_BOUNDARY_IDENTITY、路徑少於 3 點 | [src: raw/project/snapshot-20261123d/offscreen_center.py#L68-L71] |
| B worker 選定 | 路口切換器 | JUNCTION_NO_TARGET、JUNCTION_PREDICTION_NOT_CONTROL | [src: raw/project/snapshot-20261123d/junction_live.py#L181-L183] [src: raw/project/snapshot-20261123d/junction_live.py#L219-L222] |
| C 控制端最後 | live_pid（dash_route、crest_midpoint 可覆寫為有效） | 以上皆無法補救 | [src: raw/project/snapshot-20261123d/live_pid.py#L1982] [src: raw/project/snapshot-20261123d/live_pid.py#L1997] |

時間條件：
- **起跑前**：需要連續 3 格新鮮、有效的模型結果，且最新影格年齡 ≤ max_gap，才准開始 [src: raw/project/snapshot-20261123d/live_pid.py#L547]；max_gap 不可超過 0.5 s [src: raw/project/snapshot-20261123d/live_pid.py#L542]。
- **行駛中**：最終版 max_gap ＝ 0.4 s [src: raw/project/snapshot-20261123d/_extra/start_params.json#key=start.parameters.max_gap]。安全監看每 50 ms 檢查一次，最新影格比現在舊超過 max_gap 就以 PID_VISION_STALE 結束本輪 [src: raw/project/snapshot-20261123d/live_pid.py#L715-L729]。
- **每格**：本格無效或已超過 max_gap → 查失線決策表（保持、航向保持、下坡保持……，查不到就停車 PID_INVALID_OR_STALE_PATH）[src: raw/project/snapshot-20261123d/live_pid.py#L2151-L2157]。表的內容見 [[control/lost-path]]。

### 最終實跑統計（run-b541，2 圈 56.5／56.8 s）

以 `tools/stats_vision_validity.py` 自逐格紀錄 pid.jsonl（MANIFEST external 項）計算 [src: raw/records/runs/run-b541-20261123/summary.json]。紀錄只含被控制端消費、送出命令的格（2804 格、取像跨度 119.8 s），路段名是 lap_pos 的估計、不是人工標註。成績 56.5／56.8 s 出自紀錄檔 [src: raw/records/logs/AGENTS.md#L136]。

| 路段 seg | 格數 | A 基準線無效 | B worker 選定無效 | C 控制端最後無效 | C 最長連續無效 (s) |
|---|---|---|---|---|---|
| start | 1 | 0（0.0%） | 0（0.0%） | 0（0.0%） | 0.00 [src: raw/records/runs/run-b541-20261123/summary.json] |
| start_straight | 98 | 0（0.0%） | 0（0.0%） | 0（0.0%） | 0.00 [src: raw/records/runs/run-b541-20261123/summary.json] |
| curve1 | 146 | 0（0.0%） | 0（0.0%） | 0（0.0%） | 0.00 [src: raw/records/runs/run-b541-20261123/summary.json] |
| diagonal_v | 419 | 4（1.0%） | 0（0.0%） | 0（0.0%） | 0.00 [src: raw/records/runs/run-b541-20261123/summary.json] |
| curve2 | 206 | 0（0.0%） | 0（0.0%） | 0（0.0%） | 0.00 [src: raw/records/runs/run-b541-20261123/summary.json] |
| circle_straight | 221 | 0（0.0%） | 0（0.0%） | 0（0.0%） | 0.00 [src: raw/records/runs/run-b541-20261123/summary.json] |
| left_bend | 160 | 0（0.0%） | 0（0.0%） | 0（0.0%） | 0.00 [src: raw/records/runs/run-b541-20261123/summary.json] |
| curve3 | 323 | 11（3.4%） | 0（0.0%） | 0（0.0%） | 0.00 [src: raw/records/runs/run-b541-20261123/summary.json] |
| ramp | 149 | 3（2.0%） | 0（0.0%） | 0（0.0%） | 0.00 [src: raw/records/runs/run-b541-20261123/summary.json] |
| top | 121 | 0（0.0%） | 0（0.0%） | 0（0.0%） | 0.00 [src: raw/records/runs/run-b541-20261123/summary.json] |
| dashed_turn | 44 | 2（4.5%） | 8（18.2%） | 0（0.0%） | 0.00 [src: raw/records/runs/run-b541-20261123/summary.json] |
| upper_straight | 145 | 3（2.1%） | 58（40.0%） | 0（0.0%） | 0.00 [src: raw/records/runs/run-b541-20261123/summary.json] |
| upper_post | 5 | 0（0.0%） | 5（100.0%） | 5（100.0%） | 0.13 [src: raw/records/runs/run-b541-20261123/summary.json] |
| downhill | 95 | 0（0.0%） | 0（0.0%） | 1（1.1%） | 0.00 [src: raw/records/runs/run-b541-20261123/summary.json] |
| curve4 | 278 | 0（0.0%） | 0（0.0%） | 0（0.0%） | 0.00 [src: raw/records/runs/run-b541-20261123/summary.json] |
| main_straight | 388 | 7（1.8%） | 0（0.0%） | 0（0.0%） | 0.00 [src: raw/records/runs/run-b541-20261123/summary.json] |
| straight | 2 | 2（100.0%） | 2（100.0%） | 2（100.0%） | 0.03 [src: raw/records/runs/run-b541-20261123/summary.json] |
| bottom | 3 | 0（0.0%） | 0（0.0%） | 0（0.0%） | 0.00 [src: raw/records/runs/run-b541-20261123/summary.json] |
| 合計 | 2804 | 32（1.1%） | 73（2.6%） | 8（0.3%） | [src: raw/records/runs/run-b541-20261123/summary.json] |

| 路段 seg | 控制端覆寫 selected_source | B 無效原因 | C 無效時的失線處理 proposal.reason |
|---|---|---|---|
| ramp | crest_midpoint 29 | — | — [src: raw/records/runs/run-b541-20261123/summary.json] |
| top | dash_route 21、crest_midpoint 19 | — | — [src: raw/records/runs/run-b541-20261123/summary.json] |
| dashed_turn | dash_route 44 | JUNCTION_NO_TARGET 7、JUNCTION_PREDICTION_NOT_CONTROL 1 | — [src: raw/records/runs/run-b541-20261123/summary.json] |
| upper_straight | dash_route 129 | JUNCTION_NO_TARGET 49、JUNCTION_PREDICTION_NOT_CONTROL 9 | — [src: raw/records/runs/run-b541-20261123/summary.json] |
| upper_post | — | JUNCTION_NO_TARGET 5 | UPPER_SINGLE_HOLD 5 [src: raw/records/runs/run-b541-20261123/summary.json] |
| downhill | dash_route 2 | — | PID_HOLD 1 [src: raw/records/runs/run-b541-20261123/summary.json] |
| straight | — | JUNCTION_NO_TARGET 2 | PID_HOLD 2 [src: raw/records/runs/run-b541-20261123/summary.json] |

解讀：
- 平地各路段（含兩個路口）worker 選定後都沒有無效格；A 層的少數無效（例如 curve3 11 格、main_straight 7 格）都被路口走廊補上 [src: raw/records/runs/run-b541-20261123/summary.json]。
- 無效集中在高架上層：upper_straight 的 worker 選定無效率 40.0%，全部被 dash_route 覆寫；坡道與坡頂則由 crest_midpoint 補 48 格（29＋19，推算加總）[src: raw/records/runs/run-b541-20261123/summary.json]。
- 控制端最後無效只有 8 格，最長連續 0.13 s（upper_post），都低於 0.4 s，交由保持類規則處理（UPPER_SINGLE_HOLD、PID_HOLD）[src: raw/records/runs/run-b541-20261123/summary.json]。
- 這是單一輪 2 圈的統計，不代表每輪都相同。 [src: raw/records/runs/run-b541-20261123/summary.json]

## 公式與參數

- 影格過期：now − capture_at > max_gap → 過期；max_gap ＝ 0.4 s（調參值，程式上限 0.5 s）[src: raw/project/snapshot-20261123d/live_pid.py#L729] [src: raw/project/snapshot-20261123d/live_pid.py#L542] [src: raw/project/snapshot-20261123d/_extra/start_params.json#key=start.parameters.max_gap]
- 坡頂備援：ON_DEG 8°、RECENT_S 2 s、MAX_S 3 s、白線間距至少 24 px、至少 15 列、最多往上延伸 24 px（實驗值）[src: raw/project/snapshot-20261123d/crest_fallback.py#L23-L25]
- 起跑門檻：連續 3 格新鮮有效（設計值）[src: raw/project/snapshot-20261123d/live_pid.py#L547]
- 推算：控制端最後無效率 8 ÷ 2804 ＝ 0.29%；worker 選定無效率 73 ÷ 2804 ＝ 2.60%。 [src: raw/records/runs/run-b541-20261123/summary.json]

## 未確認

- 統計只涵蓋 run-b541 一輪；不同光線、電量、起點下的分布未計算。 [src: raw/records/runs/run-b541-20261123/summary.json]
- lap_pos 路段名在 `straight`（2 格）與 `bottom`（3 格）出現極少數格，其對應實際位置未逐格核對（推測是定位切換的過渡格）。 [src: raw/records/runs/run-b541-20261123/summary.json]
- 坡上／落地「約 0.5 s 中斷」是 11-19 以前的紀錄 [src: raw/records/logs/AGENTS.md#L373]，本輪 downhill 只有 1 格無效，是否已改善需更多輪次確認。

## 相關條目

- [[control/lost-path]]（無效後怎麼辦）、[[control/disabled-layers]]
- [[path/mask-to-path]]、[[path/junction-handling]]、[[path/upper-dash-route]]
- [[perception/camera-capture]]、[[perception/yolo26-sem]]、[[comms/timing-latency]]
- [[experiments/final-performance]]
