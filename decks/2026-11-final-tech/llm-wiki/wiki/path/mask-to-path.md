---
id: path/mask-to-path
title: 白線遮罩→行駛路徑→影像誤差（camera-pair-v2）
status: implemented
sources:
  - raw/project/snapshot-20261123d/_extra/start_params.json
  - raw/project/snapshot-20261123d/live_model_worker.py
  - raw/project/snapshot-20261123d/live_pid.py
  - raw/project/snapshot-20261123d/pid_paths.py
  - raw/project/snapshot-20261123d/junction_live.py
  - raw/project/snapshot-20261123d/offscreen_center.py
  - raw/project/snapshot-20261123d/camera_pair.py
  - raw/project/snapshot-20261123d/camera_pair_geometry.json
  - raw/project/snapshot-20261123d/preview_error.py
  - raw/project/snapshot-20261123d/road_state_path.py
  - raw/project/snapshot-20261123d/standalone_line_path.py
  - raw/project/snapshot-20261123d/ground_identity.py
  - raw/project/snapshot-20261123d/ground_identity.json
  - raw/project/snapshot-20261123d/camera_ground_calibration.json
  - raw/project/snapshot-20261123d/arc_fit.py
  - raw/project/snapshot-20261123d/arc2.json
  - raw/project/snapshot-20261123d/crossings_worker.json
  - raw/project/snapshot-20261123d/dash_route.py
  - raw/project/snapshot-20261123d/upper_single.json
  - raw/project/snapshot-20261123d/calibrated_path.py
  - raw/project/snapshot-20261123d/ground_road.py
  - raw/records/logs/AGENTS.md
  - raw/records/runs/run-b541-20261123/summary.json
verified_against: snapshot-20261123d
updated: 2026-11-23
---

# 白線遮罩→行駛路徑→影像誤差（camera-pair-v2）

## 一句話結論

最終版路徑演算法是 `camera-pair-v2-junction`：在 640×360 的白線遮罩上逐列找出左右白線的「內緣」，能配成一對就取中點，只看到一邊就用「車道寬比例×影像中的車道寬」往內推半個車道，得到一條行駛中心線；控制端在固定的影像高度 0.6 處讀這條線相對畫面中央的橫向偏移（誤差 −1～+1），再加上低通的「遠方方向」項，交給 PID [src: raw/project/snapshot-20261123d/_extra/start_params.json#key=start.path_algorithm] [src: raw/project/snapshot-20261123d/standalone_line_path.py#L213-L217] [src: raw/project/snapshot-20261123d/preview_error.py#L94-L100]。全程以「影像像素比例」計算，地面公分座標（單應性）只用在幾個輔助模組。

## 內容

### 選用哪個演算法

- 起跑參數 `path_algorithm` 為 `camera-pair-v2-junction-flag` [src: raw/project/snapshot-20261123d/_extra/start_params.json#key=start.path_algorithm]；它只是「從旗子位置起跑」的別名，控制端與 worker 都換回 `camera-pair-v2-junction` [src: raw/project/snapshot-20261123d/live_pid.py#L199] [src: raw/project/snapshot-20261123d/pid_paths.py#L6]。
- worker 對 `camera-pair-v2-junction` 建立 `JunctionLine` [src: raw/project/snapshot-20261123d/live_model_worker.py#L195]。類別階層：JunctionLine → OffscreenLine → CameraPairLine → PreviewErrorLine → RoadStateLine [src: raw/project/snapshot-20261123d/junction_live.py#L55] [src: raw/project/snapshot-20261123d/offscreen_center.py#L61] [src: raw/project/snapshot-20261123d/camera_pair.py#L89] [src: raw/project/snapshot-20261123d/preview_error.py#L13]。
- `ground_identity.json` 開啟，所以基準估計器換成 `GroundIdentityEstimate`（以地面公分座標判斷哪條線是左／右，見下表）[src: raw/project/snapshot-20261123d/ground_identity.json#key=enabled] [src: raw/project/snapshot-20261123d/junction_live.py#L69-L72] [src: raw/project/snapshot-20261123d/ground_identity.py#L60]。

### 步驟一：遮罩→白線軌跡（640×360）

1. 遮罩縮成 640×360，在第 140～340 列、每 4 列取樣（共 51 列）找白色連續段（run）[src: raw/project/snapshot-20261123d/standalone_line_path.py#L26] [src: raw/project/snapshot-20261123d/standalone_line_path.py#L257]。推算：range(140, 344, 4) 共 (344−140)/4 ＝ 51 列。
2. 各列的段連成「軌跡」（track），依斜率／位置標成左（L）或右（R）；無法判斷者用底部 x 位置（< 250 為左、> 390 為右）[src: raw/project/snapshot-20261123d/camera_pair.py#L28-L34]。
3. **取內緣**：每個軌跡點移到該白色段靠車道那一側的邊緣（左線取右緣、右線取左緣）[src: raw/project/snapshot-20261123d/camera_pair.py#L35-L38]。原因：路面車道寬是以內緣對內緣量的（46 cm）[src: raw/project/snapshot-20261123d/camera_ground_calibration.json#key=ground_frame]。

### 步驟二：左右配對

對每一組（左軌跡, 右軌跡）[src: raw/project/snapshot-20261123d/camera_pair.py#L45-L62]：

- 共同列至少 7 列、跨度至少 24 px，否則拒絕（SHORT_SHARED_SUPPORT）。 [src: raw/project/snapshot-20261123d/camera_pair.py#L52-L53]
- 每列算寬度比 ratio ＝（x_R − x_L）÷ width(y)，width(y) 是 `camera_pair_geometry.json` 以實地膠帶點擬合的「該列應有車道寬」[src: raw/project/snapshot-20261123d/camera_pair.py#L9-L12]。
- 有任一列 ratio ≤ 0 → 交叉（CROSSING）；中位數不在 0.65～1.45 → 寬度不符（WIDTH_PROFILE）；第 90 與第 10 百分位差 > 0.20 → 發散（DIVERGING_PROFILE，例如岔路口張開）。 [src: raw/project/snapshot-20261123d/camera_pair.py#L54-L58]
- 合格者以 |中位數 − 1| + 發散度 評分取最小；分數相差 0.05 內時，以與上一格位置的接近程度決勝 [src: raw/project/snapshot-20261123d/camera_pair.py#L64-L74]。
- 沒有合格對 → 退回只用一側（較長的那條）[src: raw/project/snapshot-20261123d/camera_pair.py#L75-L82]。
- 若同時有多個合格對、但和上一格的左右身分對不上 → 判為「身分不明」，整格路徑作廢（AMBIGUOUS_BOUNDARY_IDENTITY）[src: raw/project/snapshot-20261123d/offscreen_center.py#L32-L45] [src: raw/project/snapshot-20261123d/offscreen_center.py#L68-L71]。

### 步驟三：中心線

在每個取樣列 [src: raw/project/snapshot-20261123d/standalone_line_path.py#L213-L219]：
- 兩側都有 → 中點（來源記為 double）；
- 只有右線 → x_R − k·width(y)/2；只有左線 → x_L + k·width(y)/2。 [src: raw/project/snapshot-20261123d/standalone_line_path.py#L216-L217]

其中 k 是「最近觀察到的寬度比」：有兩側時取各列 ratio 中位數並夾在 0.7～1.4 [src: raw/project/snapshot-20261123d/standalone_line_path.py#L200]；這個值記憶 30 s，實際套用值每秒最多變 0.3 [src: raw/project/snapshot-20261123d/standalone_line_path.py#L34] [src: raw/project/snapshot-20261123d/standalone_line_path.py#L201-L206]。中心點允許落在畫面外（OffscreenEstimate 的 allow_offscreen）[src: raw/project/snapshot-20261123d/offscreen_center.py#L31]。接著做 3 點中位數平滑、斷點（列差 > 12 或 x 差 > 40）切段，取最長一段，並把座標乘 2 回到 1280×720 [src: raw/project/snapshot-20261123d/standalone_line_path.py#L220-L234]。至少 3 點才算有效 [src: raw/project/snapshot-20261123d/standalone_line_path.py#L265]。

最終實跑中，worker 送出的診斷記錄了每列中心的來源（例如 double 45、left+width 6），可看出單線推算所占比例；統計見 [[path/vision-failure-modes]]。

### 步驟四：影像誤差（控制端）

控制器為 `OffscreenPID`（固定取樣列）[src: raw/project/snapshot-20261123d/offscreen_center.py#L75-L84]：

- 近點誤差 e_near：路徑在影像高度 row ＝ 0.6×719 處的 x，相對「畫面中心＋視覺中心偏移」正規化到 −1～+1 [src: raw/project/snapshot-20261123d/offscreen_center.py#L20-L28]；row_ratio 0.6、visual_center_offset_px_640 ＝ 18 [src: raw/project/snapshot-20261123d/_extra/start_params.json#key=start.parameters.row_ratio] [src: raw/project/snapshot-20261123d/_extra/start_params.json#key=start.parameters.visual_center_offset_px_640]。
- 遠點誤差 e_far：同一路徑在 far_row ＝ 0.45 處的誤差，先乘 width(近)/width(遠) 做「透視正規化」，避免平行但偏移的車道因透視收斂被誤當成方向誤差 [src: raw/project/snapshot-20261123d/preview_error.py#L56-L66] [src: raw/project/snapshot-20261123d/_extra/start_params.json#key=start.parameters.preview_far_row]。
- 方向項：raw ＝ far_weight ×（e_far_proj − e_near），far_weight ＝ 0.2，經時間常數 0.15 s 的一階低通 [src: raw/project/snapshot-20261123d/preview_error.py#L95-L99] [src: raw/project/snapshot-20261123d/_extra/start_params.json#key=start.parameters.preview_far_weight] [src: raw/project/snapshot-20261123d/preview_error.py#L53-L54]；格間隔 ≤ 0 或 > max_gap（0.4 s）、或沒有遠點時，方向項歸零 [src: raw/project/snapshot-20261123d/preview_error.py#L96-L97]。
- 控制誤差 ＝ clip(e_near ＋ 方向項, −1, 1)，送進 PID；PID 的微分項改用「近點位置的變化」以免遠點抖動被放大 [src: raw/project/snapshot-20261123d/preview_error.py#L25-L35] [src: raw/project/snapshot-20261123d/preview_error.py#L100-L102]。PID 本身見 [[control/pid-core]]。

### 地面單應性（像素→地面公分）在最終版用在哪裡

**單應性（homography）**：一個 3×3 矩陣，把「平地上的點在影像中的像素位置」換算成「車前方幾公分、偏左右幾公分」；只在地面平坦、鏡頭姿態不變時成立。最終版有效的一份是 `camera_ground_calibration.json`（camera-ground-20261109-r2，640×360，原點為前輪最前緣、x 為車道中心右方公分；擬合 RMSE 1.087 cm）[src: raw/project/snapshot-20261123d/camera_ground_calibration.json#key=version] [src: raw/project/snapshot-20261123d/camera_ground_calibration.json#key=ground_frame] [src: raw/project/snapshot-20261123d/camera_ground_calibration.json#key=fit.rmse_cm]。

| 呼叫點 | 用途 | 最終版是否作用 | 依據 |
|---|---|---|---|
| ground_identity（worker） | 把上一格左右線依車速、gz 移動後與本格在地面座標比對，決定單線是左還是右 | 是（enabled true） | [src: raw/project/snapshot-20261123d/ground_identity.py#L1-L8] [src: raw/project/snapshot-20261123d/ground_identity.json#key=enabled] |
| arc_fit（worker） | 白線中心在地面上的曲率、方向、車到內緣距離 | 是（crossings_worker.json 的 arc_fit 開啟） | [src: raw/project/snapshot-20261123d/arc_fit.py#L1-L13] [src: raw/project/snapshot-20261123d/crossings_worker.json#key=arc_fit.enabled] |
| 彎 3 距離帶狀（arc2 c3.xband） | 用 arc_lat 的橫向位置 y 修正舵量，k_y_us 5.0 | 是（控制層，詳見 [[control/curve-band-ff]]） | [src: raw/project/snapshot-20261123d/arc2.json#key=c3.xband.k_y_us] |
| dash_route 的 range_start | 把虛線橫列投影到地面，算距前輪幾公分，決定何時起轉 | 是 | [src: raw/project/snapshot-20261123d/dash_route.py#L300-L337] |
| upper_single 的 edge_source／hold_dir_fit | 高架上層兩側實線位置、虛線方向角 | 是（edge_source、hold_dir_fit 為 true；mask_dash 為 false） | [src: raw/project/snapshot-20261123d/upper_single.json#key=edge_source] [src: raw/project/snapshot-20261123d/upper_single.json#key=mask_dash] [src: raw/project/snapshot-20261123d/live_pid.py#L234-L235] |
| calibrated_path（calibration_v7.json） | 舊的「calibrated-v7」路徑演算法 | 否，只在選用該演算法時載入 | [src: raw/project/snapshot-20261123d/live_model_worker.py#L342-L345] [src: raw/project/snapshot-20261123d/calibrated_path.py#L17] |
| ground_road（ground_road_calibration.json） | 舊的「straight-bearing-v1」控制器 | 否 | [src: raw/project/snapshot-20261123d/ground_road.py#L39] [src: raw/project/snapshot-20261123d/live_pid.py#L567] |

主線的左右配對寬度用的是 `camera_pair_geometry.json`——這是影像列上的寬度直線擬合（50／80／120 cm 三列膠帶點，`metric_calibrated` false），不是單應性 [src: raw/project/snapshot-20261123d/camera_pair_geometry.json#key=snapshot.metric_calibrated] [src: raw/project/snapshot-20261123d/camera_pair.py#L10-L12]。

### 短時預測在最終版被擋掉

RoadStateLine 原本會在遮罩幾乎沒有白線（≤ 20 px）時，以 0.15 s 內的可靠路徑外推作為預測路徑 [src: raw/project/snapshot-20261123d/road_state_path.py#L86-L98]；但 OffscreenLine 隨後規定「沒有本格看到的邊界就作廢，不用舊路徑補」[src: raw/project/snapshot-20261123d/offscreen_center.py#L68-L71]。推論：在 camera-pair-v2 主線上，這個預測實際上不會被當成有效路徑（以程式流程推得，未以紀錄逐格驗證）。

## 公式與參數

- width(y) ＝ max(20, (r₀ − l₀)·y + r₁ − l₁)，(l₀,l₁)＝(−1.4707, 420.857)、(r₀,r₁)＝(1.7013, 236.354)（實測膠帶點擬合值）[src: raw/project/snapshot-20261123d/camera_pair.py#L10-L12] [src: raw/project/snapshot-20261123d/camera_pair_geometry.json#key=fits]
- 中心：x_c ＝ (x_L + x_R)/2；單線時 x_c ＝ x_R − k·width(y)/2 或 x_L + k·width(y)/2；k ∈ [0.7, 1.4]，記憶 30 s、變化率 0.3/s（調參值）[src: raw/project/snapshot-20261123d/standalone_line_path.py#L200] [src: raw/project/snapshot-20261123d/standalone_line_path.py#L213-L217] [src: raw/project/snapshot-20261123d/standalone_line_path.py#L34]
- 配對門檻：共同 ≥ 7 列、跨度 ≥ 24 px；ratio 中位數 0.65～1.45；發散度 ≤ 0.20（實驗值，程式註明「不是安全門檻」）[src: raw/project/snapshot-20261123d/camera_pair.py#L52-L58]
- 近點誤差：e ＝ (x − 639.5 − offset×2) ÷ 639.5，取 clip(−1, 1)；offset ＝ 18 px（640 尺度，調參值）[src: raw/project/snapshot-20261123d/offscreen_center.py#L26-L27] [src: raw/project/snapshot-20261123d/_extra/start_params.json#key=start.parameters.visual_center_offset_px_640]
- 遠點透視正規化：e_far_proj ＝ e_far × width(y_near)/width(y_far) [src: raw/project/snapshot-20261123d/preview_error.py#L64]
- 方向項低通：d ← d + dt/(τ+dt)·(0.2·(e_far_proj − e_near) − d)，τ ＝ 0.15 s（調參值）[src: raw/project/snapshot-20261123d/preview_error.py#L95-L99]
- 控制誤差：e_ctrl ＝ clip(e_near + d, −1, 1) [src: raw/project/snapshot-20261123d/preview_error.py#L100]
- 取樣列 row_ratio 0.6、far_row 0.45、far_weight 0.2（調參值）[src: raw/project/snapshot-20261123d/_extra/start_params.json#key=start.parameters.row_ratio] [src: raw/project/snapshot-20261123d/_extra/start_params.json#key=start.parameters.preview_far_row] [src: raw/project/snapshot-20261123d/_extra/start_params.json#key=start.parameters.preview_far_weight]
- 推算：row 0.6 對應 1280×720 的第 0.6×719 ＝ 431.4 列，640×360 的第 215.7 列。 [src: raw/project/snapshot-20261123d/_extra/start_params.json#key=start.parameters.row_ratio]

## 未確認

- `camera_pair_geometry.json` 的寬度擬合來自 10-30 的鏡頭姿態（camera-inner-20261030-r1）[src: raw/project/snapshot-20261123d/camera_pair_geometry.json#key=revision]，之後鏡頭有調整過；它是否仍貼合最終姿態，原始資料只有「鏡頭核對通過」的間接證據 [src: raw/records/logs/AGENTS.md#L99]。
- 單應性的姿態假設：檔內寫「current fixed view (user, 2026-11-09 evening)」[src: raw/project/snapshot-20261123d/camera_ground_calibration.json#key=camera_pose]；之後撞車、換舵機後是否重做未見紀錄。
- 直線接續器（LiveConnectorLine，straight-connector-live-r1）在最終實跑樣本中顯示未套用（V3_NOT_IN_STRAIGHT_APPROACH），其在哪些路段會作用未逐一追查。 [src: raw/records/runs/run-b541-20261123/summary.json]
- 「推論」標記的短時預測失效，未以逐格紀錄驗證。

## 相關條目

- [[perception/yolo26-sem]]、[[perception/camera-capture]]
- [[path/junction-handling]]（路口時改用透視走廊）、[[path/upper-dash-route]]（高架上層改用虛線）、[[path/vision-failure-modes]]
- [[control/pid-core]]、[[control/command-chain]]、[[control/curve-band-ff]]
