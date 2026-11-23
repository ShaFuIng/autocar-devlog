---
id: path/upper-dash-route
title: 高架上層虛線路段（DashRoute 狀態機與虛線轉彎觸發）
status: implemented
sources:
  - raw/project/snapshot-20261123d/dash_route.py
  - raw/project/snapshot-20261123d/upper_turn.json
  - raw/project/snapshot-20261123d/upper_single.json
  - raw/project/snapshot-20261123d/upper_single.py
  - raw/project/snapshot-20261123d/dash_fast.json
  - raw/project/snapshot-20261123d/live_pid.py
  - raw/project/snapshot-20261123d/mask_dash.py
  - raw/project/snapshot-20261123d/imu_boost.json
  - raw/project/docs/track-map-01-12.webp
  - raw/records/logs/AGENTS.md
  - raw/records/runs/run-b541-20261123/summary.json
verified_against: snapshot-20261123d
updated: 2026-11-23
---

# 高架上層虛線路段（DashRoute 狀態機與虛線轉彎觸發）

## 一句話結論

爬上 09 的藍色坡道後是一段高架上層，車要在白色虛線處左轉（地圖 10，「捷徑」），之後沿虛線把兩條車道隔開的方向直行，再下坡到 11 [src: raw/records/logs/AGENTS.md#L6] [src: raw/project/docs/track-map-01-12.webp]。最終版用 `dash_route.py`（dash-route-r27）的狀態機：IMU 判斷「爬過坡、回到平地」後開啟路線窗（OPEN），窗內每格在 JPEG 上找虛線色塊，先以「橫向一排虛線」觸發左轉（TURN），再沿虛線本身前進（FOLLOW），並以這條虛線路徑覆寫普通的白線路徑；轉彎何時開始由距離（range_start）、位置下限（start_gate）與位置備援（pos_backup，TOP 後 2.5 m）共同決定 [src: raw/project/snapshot-20261123d/dash_route.py#L1-L22] [src: raw/project/snapshot-20261123d/upper_turn.json#key=pos_backup.after_m] [src: raw/project/snapshot-20261123d/live_pid.py#L1982]。轉完之後的轉向控制（陀螺儀航向＋虛線橫向）見 [[control/heading-hold]]。

## 內容

### 狀態機（路線窗）

由 IMU 相對俯仰（pitch_rel＝pitch − flat_pitch_deg）驅動 [src: raw/project/snapshot-20261123d/dash_route.py#L762-L771]：

| 狀態 | 進入下一狀態的條件 | 依據 |
|---|---|---|
| WAIT_CLIMB | pitch_rel ≥ 8° 持續 2 s → CLIMBED | [src: raw/project/snapshot-20261123d/dash_route.py#L772-L776] |
| CLIMBED | pitch_rel < 3° 持續 0.5 s → OPEN（記下開啟時間） | [src: raw/project/snapshot-20261123d/dash_route.py#L777-L781] |
| OPEN | pitch_rel ≤ −5°（開始下坡）或開啟超過 60 s → DONE | [src: raw/project/snapshot-20261123d/dash_route.py#L782-L784] |
| DONE | 先看到 pitch_rel ≤ −10°，之後 |pitch_rel| < 3° 持續 3 s → 回 WAIT_CLIMB，圈數 +1 | [src: raw/project/snapshot-20261123d/dash_route.py#L785-L795] |

門檻常數 [src: raw/project/snapshot-20261123d/dash_route.py#L373] [src: raw/project/snapshot-20261123d/dash_route.py#L503]。IMU 讀不到或超過 max_age_s 就維持目前狀態並記錄 IMU_UNAVAILABLE／IMU_STALE [src: raw/project/snapshot-20261123d/dash_route.py#L765-L771]。統一地圖說明 WAIT_CLIMB→CLIMBED→OPEN 對應 09 坡道→上段、虛線轉彎＝10、DONE＝下坡往 11 [src: raw/records/logs/AGENTS.md#L8]。

### 窗內每格：找虛線

- 影像：同一格 JPEG 縮成 640×360；「白」＝亮（V ≥ 185）且不飽和（S ≤ 60），只看第 100 列以下；虛線方塊＝面積 25～9000 的緊湊連通區塊 [src: raw/project/snapshot-20261123d/dash_route.py#L13-L17] [src: raw/project/snapshot-20261123d/dash_route.py#L374] [src: raw/project/snapshot-20261123d/dash_route.py#L824-L826]。
- 虛線＝至少 3 個共線方塊（RANSAC 擬合），且至少一塊在第 175 列（NEAR_Y）以下 [src: raw/project/snapshot-20261123d/dash_route.py#L15-L17]。
- **白色門檻隨亮度（white_rel，開）**：轉彎前，把第 100～175 列的中位亮度＋30 當白色門檻（夾在 185～235），使暗天、亮天的偵測一致 [src: raw/project/snapshot-20261123d/upper_turn.json#key=white_rel] [src: raw/project/snapshot-20261123d/upper_turn.json#key=note]。
- 等值加速版 dash_fast 開啟（結果相同、少算一次） [src: raw/project/snapshot-20261123d/dash_fast.json#key=enabled] [src: raw/project/snapshot-20261123d/dash_route.py#L61-L71]。

### TURN 與 FOLLOW

- **ACROSS（橫向列，與水平夾角 < 35°）** 在未轉彎前代表「虛線橫在前方」：通過起轉品質檢查後進入 TURN，路徑由車軸（x＝338）畫向這排虛線的最左端 [src: raw/project/snapshot-20261123d/dash_route.py#L392] [src: raw/project/snapshot-20261123d/dash_route.py#L889-L891] [src: raw/project/snapshot-20261123d/dash_route.py#L550]。
- **ALONG（縱向）** 在轉彎後代表「沿著虛線」：進入 FOLLOW，路徑沿擬合的虛線一路畫到畫面底部 [src: raw/project/snapshot-20261123d/dash_route.py#L892-L908]。轉彎前看到縱向虛線不跟（ALONG_BEFORE_TURN）[src: raw/project/snapshot-20261123d/dash_route.py#L894]。
- FOLLOW 之後再出現橫向列一律忽略，只保持上一個目標（FOLLOW_LOCK）[src: raw/project/snapshot-20261123d/dash_route.py#L857-L862]。
- 方向閘：FOLLOW 時虛線方向若與航向保持給的預期方向差超過閘門（預設 10°）→ DIRECTION_MISMATCH，不採用 [src: raw/project/snapshot-20261123d/dash_route.py#L898-L905] [src: raw/project/snapshot-20261123d/dash_route.py#L465]。
- 沒看到虛線時，0.5 s 內保持上一個目標（HOLD_LAST），之後放手給一般路徑 [src: raw/project/snapshot-20261123d/dash_route.py#L843-L848] [src: raw/project/snapshot-20261123d/dash_route.py#L392]。
- 控制列上的目標 x 每秒最多移動 300 px，避免兩排虛線交界時跳動 [src: raw/project/snapshot-20261123d/dash_route.py#L920-L923] [src: raw/project/snapshot-20261123d/dash_route.py#L392]。
- live_pid 在輪次進行中、路線窗 OPEN 時呼叫 `try_path`；有虛線路徑就把本格路徑換成它並標 `selected_source='dash_route'`、valid 設為 true [src: raw/project/snapshot-20261123d/live_pid.py#L1964-L1983]。所以即使 worker 端（路口切換器）判定無效，這一格仍可能有效，見 [[path/vision-failure-modes]]。

### 虛線轉彎何時開始（upper_turn.json）

三套規則同時作用 [src: raw/project/snapshot-20261123d/upper_turn.json#key=note]：

1. **距離起轉 range_start（開）**：把橫向列的方塊中心用地面單應性投影成「這排虛線在前輪前方幾公分」R；連續觀察確認後，當 R ≤ R0 ＝ a + b·v 時起轉，a 0.521、b 0.46、v 為輪速（夾在 0.4～1.0 m/s）[src: raw/project/snapshot-20261123d/dash_route.py#L300-L323] [src: raw/project/snapshot-20261123d/upper_turn.json#key=range_start]。例：0.78 m/s 時 R0 ＝ 0.521 + 0.46×0.78 ＝ 0.880 m（推算）。11-19 現場把 a 由 0.471 調到 0.521，讓起轉提早約 5 cm [src: raw/project/snapshot-20261123d/upper_turn.json#key=note_range_field]。
2. **太早不准起轉 start_gate（開）**：若 lap_pos 顯示離坡頂（TOP）< 2.2 m、且本路線窗自己的里程 < 1.8 m，就拒絕相機起轉——用來擋地墊接縫被誤認成虛線列 [src: raw/project/snapshot-20261123d/upper_turn.json#key=start_gate] [src: raw/project/snapshot-20261123d/dash_route.py#L47-L59]。
3. **位置備援 pos_backup（開）**：相機到 TOP 後 2.5 m 仍未起轉，而且 lap_pos 未失鎖、|俯仰| < 3°、距 TOP < 4.0 m，就以位置直接起轉，目標 x＝139 px [src: raw/project/snapshot-20261123d/upper_turn.json#key=pos_backup] [src: raw/project/snapshot-20261123d/dash_route.py#L805-L815]。

最終設定的由來：11-23 換新舵機後虛線轉彎變晚，常靠舊的 2.9 m 位置備援才起轉 [src: raw/records/logs/AGENTS.md#L149]；先改 2.65 [src: raw/records/logs/AGENTS.md#L145]，再改 2.5（與補償 ±15 同時）後 run-ce19 虛線轉彎 3/3 轉完、起轉在 TOP+2.57～2.62 m [src: raw/records/logs/AGENTS.md#L143-L144]。

### 轉完之後（只列與路徑有關的部分）

- `upper_single.json` 開啟，轉彎結束到路線窗關閉之間由單一轉向律接管（ALIGN→FOLLOW→HOLD，或 one 律）[src: raw/project/snapshot-20261123d/upper_single.json#key=enabled] [src: raw/project/snapshot-20261123d/upper_single.py#L1-L10]；控制細節見 [[control/heading-hold]]。
- 其路徑來源：FOLLOW 的虛線擬合（dash_route）優先；`edge_source` 開啟，worker 另外偵測上層兩側實線邊緣點（upper_edges）給橫向估計 [src: raw/project/snapshot-20261123d/upper_single.json#key=edge_source] [src: raw/project/snapshot-20261123d/upper_single.py#L22-L26]。
- 遮罩虛線偵測 `mask_dash` 關閉；只因 `hold_dir_fit` 開啟而建立它的角度輔助（不做 find）[src: raw/project/snapshot-20261123d/upper_single.json#key=mask_dash] [src: raw/project/snapshot-20261123d/upper_single.json#key=hold_dir_fit] [src: raw/project/snapshot-20261123d/live_pid.py#L234-L235]。

### 上層幾何（使用者實量）

兩邊線間距 102 cm（虛線最後一格前 45 cm）→ 92 cm（最後一格處）→ 54 cm（坡口），最後一格到坡口 120 cm [src: raw/records/logs/AGENTS.md#L113]。上層是一個往下坡口收窄的漏斗。

### 最終實跑中的情形（run-b541）

由 tools/stats_vision_validity.py 自逐格紀錄 pid.jsonl（MANIFEST external 項）計算 [src: raw/records/runs/run-b541-20261123/summary.json]：

| 路段 | 格數 | worker 選定無效 | 控制端覆寫為 dash_route | 控制端最後無效 |
|---|---|---|---|---|
| top（坡頂） | 121 | 0 | 21 | 0 [src: raw/records/runs/run-b541-20261123/summary.json] |
| dashed_turn（虛線轉彎） | 44 | 8 | 44 | 0 [src: raw/records/runs/run-b541-20261123/summary.json] |
| upper_straight（轉彎後上層直線） | 145 | 58 | 129 | 0 [src: raw/records/runs/run-b541-20261123/summary.json] |
| upper_post | 5 | 5 | 0 | 5（UPPER_SINGLE_HOLD） [src: raw/records/runs/run-b541-20261123/summary.json] |
| downhill | 95 | 0 | 2 | 1 [src: raw/records/runs/run-b541-20261123/summary.json] |

上層 worker 端的無效原因多為 JUNCTION_NO_TARGET（路口切換器找不到目標）與 JUNCTION_PREDICTION_NOT_CONTROL；這些格被虛線路徑覆寫後仍可控制。upper_post 的 5 格無虛線可用，交給 upper_single 的保持律 [src: raw/records/runs/run-b541-20261123/summary.json]。

## 公式與參數

- 路線窗：CLIMB 8°／2 s、LEVEL 3°／0.5 s、DOWN −5°、WINDOW 60 s、REARM −10°／3 s（實驗值）[src: raw/project/snapshot-20261123d/dash_route.py#L373] [src: raw/project/snapshot-20261123d/dash_route.py#L503]
- 白色：V ≥ 185、S ≤ 60、y ≥ 100；NEAR_Y 175；方塊面積 25～9000（實驗值）[src: raw/project/snapshot-20261123d/dash_route.py#L374]
- 橫向判定 ACROSS_DEG 35°、LOST_S 0.5 s、MAX_SHIFT 300 px/s；起轉品質 START_DEG 15°／至少 4 塊（實驗值）[src: raw/project/snapshot-20261123d/dash_route.py#L392] [src: raw/project/snapshot-20261123d/dash_route.py#L396]
- 起轉距離 R0 ＝ a + b·v，a ＝ 0.521 m（現場調參）、b ＝ 0.46 s（29 次轉彎擬合）[src: raw/project/snapshot-20261123d/upper_turn.json#key=range_start] [src: raw/project/snapshot-20261123d/dash_route.py#L322-L323]
- 位置備援 after_m 2.5 m、max_m 4.0 m、x_row 139 px、max_pitch 3°（調參值）[src: raw/project/snapshot-20261123d/upper_turn.json#key=pos_backup]
- start_gate min_top_m 2.2、min_open_m 1.8（依 140 次正常起轉 TOP+2.44～2.88 m 的分布選定）[src: raw/project/snapshot-20261123d/upper_turn.json#key=start_gate] [src: raw/project/snapshot-20261123d/dash_route.py#L57-L58]

## 未確認

- range_start 依賴 11-09 的地面單應性；檔內註明「今天的姿態下方正的一排會量成約 −35° 的地面角，屬姿態誤差，因此只取 x＝0 處的 R，R0 依結果校正而非絕對距離」[src: raw/project/snapshot-20261123d/dash_route.py#L307-L309]。換舵機後的鏡頭姿態是否仍一致未見核對。
- 新舵機時代虛線轉彎「60° 用時」比舊舵機長（1.41～1.55 s 對 1.27～1.41 s）[src: raw/records/logs/AGENTS.md#L145]，最終設定下的完整統計未做。

## 相關條目

- [[control/heading-hold]]（轉完後的航向保持與上層橫向）、[[control/slope-downhill]]、[[control/lap-position]]
- [[hardware/imu-mpu6050]]、[[path/mask-to-path]]、[[path/vision-failure-modes]]
