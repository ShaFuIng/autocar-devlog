---
id: path/junction-handling
title: 路口與交叉處的路徑選擇（透視走廊＋切換器）
status: implemented
sources:
  - raw/project/snapshot-20261123d/junction_live.py
  - raw/project/snapshot-20261123d/junction_corridor.py
  - raw/project/snapshot-20261123d/junction_corridor_default.json
  - raw/project/snapshot-20261123d/junction_switch.py
  - raw/project/snapshot-20261123d/crossings_worker.py
  - raw/project/snapshot-20261123d/crossings_worker.json
  - raw/project/snapshot-20261123d/ground_identity.py
  - raw/project/docs/track-map-01-12.webp
  - raw/records/logs/AGENTS.md
  - raw/records/runs/run-b541-20261123/summary.json
verified_against: snapshot-20261123d
updated: 2026-11-23
---

# 路口與交叉處的路徑選擇（透視走廊＋切換器）

## 一句話結論

跑道有兩處與其他路段平面交叉（02→03 斜線與 04→05 直線都穿過圓圈），白線在這裡會岔開、交叉或中斷，普通的左右配對可能抓到別條線；最終版在 worker 裡同時跑一個「透視走廊」追蹤器，並由切換器決定這一格用「基準路徑」還是「走廊路徑」——走廊只有在兩側都有強支持、且和基準路徑明顯不一致，或基準路徑在控制列沒有目標時才接手 [src: raw/project/snapshot-20261123d/junction_live.py#L1-L16] [src: raw/project/snapshot-20261123d/junction_switch.py#L1-L23] [src: raw/records/logs/AGENTS.md#L6-L8]。本頁只談「路徑怎麼選」；路口內的航向保持控制見 [[control/heading-hold]]。

## 內容

### 路口在跑道上的位置

統一地圖上，車從 02 往左下斜線行駛時經過 1F 隧道並與圓圈平面交叉；04→05 的往右直線也穿過圓圈交叉 [src: raw/records/logs/AGENTS.md#L6] [src: raw/project/docs/track-map-01-12.webp]。控制端對應的窗口：彎 2 結束後 0.4～2.2 m（04→05）、彎 1 結束後 3.0～4.6 m（02→03）[src: raw/records/logs/AGENTS.md#L8]。在逐格紀錄裡這兩段的 lap_pos 路段名是 `diagonal_v`（斜線 V 字路口）與 `circle_straight`（圓圈直線）[src: raw/records/runs/run-b541-20261123/summary.json]（由 tools/stats_vision_validity.py 自 pid.jsonl 讀出）。

### 透視走廊（junction_corridor.py，r1.9）

- **模型**：把平地上的一條車道在 640×360 遮罩中描述成兩條經過同一個消失點的直線：中心 center(y) ＝ v_x + s·(y − y_h)，半寬 half(y) ＝ k·a·(y − y_h)/2；y_h（地平線列）與 a（寬度斜率）由起跑後頭三格「兩側都看得到」的直線入口擬合 [src: raw/project/snapshot-20261123d/junction_corridor.py#L1-L13]。
- **搜尋**：每格在上一格狀態附近搜尋（v_x, x216, k），分數＝邊界支持數減去走廊內部的白色像素數；因為「一條邊界＋寬度模型」就能決定走廊，路口一側張開時走廊不必換畫法 [src: raw/project/snapshot-20261123d/junction_corridor.py#L7-L11]。只用本格遮罩、時間與自己過去的狀態，不看未來幀、不送命令 [src: raw/project/snapshot-20261123d/junction_corridor.py#L13-L14]。
- **預設校正**：若 1.0 s 內沒有現場校正（例如起點只看得到一條線），改用存檔的現行姿態預設（horizon_y 55.36、width_slope 3.3058），但要求至少一側邊界有 40 列且車在走廊內才採用 [src: raw/project/snapshot-20261123d/junction_corridor.py#L131-L140] [src: raw/project/snapshot-20261123d/junction_corridor_default.json#key=horizon_y] [src: raw/project/snapshot-20261123d/junction_corridor_default.json#key=width_slope]。
- worker 先把模型遮罩縮成 640×360 再給走廊 [src: raw/project/snapshot-20261123d/junction_live.py#L151-L153]。

### 切換器（junction_switch.py，fallback-handback-r12）

**支持程度**：走廊兩側都有、且兩側列數都 ≥ N（20）→ strong；只有一側或列數不足 → weak；沒影像只靠模型滑行（COAST）→ predicted；其餘 → none [src: raw/project/snapshot-20261123d/junction_switch.py#L89-L92] [src: raw/project/snapshot-20261123d/junction_switch.py#L68-L69]。

**狀態** [src: raw/project/snapshot-20261123d/junction_switch.py#L10-L23]：

| 狀態 | 目標 | 對外的來源名 |
|---|---|---|
| FOLLOW | 基準路徑（[[path/mask-to-path]]） | baseline |
| TAKEN | 有本格影像支持的走廊路徑 | corridor |
| PREDICT | 沒有本格支持的走廊模型路徑，最多 0.4 s | corridor_predicted（不可用於控制） [src: raw/project/snapshot-20261123d/junction_switch.py#L68-L69] |
| NO_TARGET | 沒有目標 | None |

**接手條件**：
1. FOLLOW 時，走廊 strong 且在控制列與基準相差 > D（80 px）→ TAKEN（STRONG_CORRIDOR_DISAGREES）[src: raw/project/snapshot-20261123d/junction_switch.py#L117-L118] [src: raw/project/snapshot-20261123d/junction_switch.py#L132-L134]。
2. 基準在控制列沒有目標、走廊 strong 且不是 OFF_CORRIDOR、剩下的基準路徑最低列與走廊差 ≤ D → TAKEN（BASELINE_NO_PATH_CORRIDOR，fallback）[src: raw/project/snapshot-20261123d/junction_switch.py#L189-L212]。
3. 方向感知接手：走廊 strong 且在控制列上下的「方向檢查列」差 > 70 px 連續 5 格 → 也接手；用來處理「控制列只差 25～60 px、但上方差 70～99 px」的岔路 [src: raw/project/snapshot-20261123d/junction_switch.py#L215-L232]。

**交還條件**：連續 3 格（AGREE_FRAMES）走廊有支持、基準有效、控制列差 ≤ 20 px、方向列差 ≤ 30 px，而且基準在「本格」走廊邊界內 → 回到 FOLLOW（BASELINE_REJOINED）[src: raw/project/snapshot-20261123d/junction_switch.py#L16-L22] [src: raw/project/snapshot-20261123d/junction_switch.py#L111-L115]。只剩單側支持時不交還而是繼續 TAKEN；現場版把弱支持可維持的時間 WEAK_S 由 1.0 s 放寬為 2.0 s [src: raw/project/snapshot-20261123d/junction_live.py#L36-L42]。

**有效性**：選到基準→沿用基準的有效性；選到走廊→走廊路徑要涵蓋控制列；預測路徑只顯示與記錄、不算有效，所以 0.4 s 失線停止計時從最後一格有支持的影像算起 [src: raw/project/snapshot-20261123d/junction_live.py#L8-L13] [src: raw/project/snapshot-20261123d/junction_live.py#L181-L183]。

### worker 端附加規則（crossings_worker.json，每次載入模型時讀）

| 鍵 | 作用（簡述） | 最終值 | 依據 |
|---|---|---|---|
| amb_one_side | 多組配對身分不明、但恰有一側與上一格連續時，只用那一側（不留空窗、不觸發走廊 fallback） | true | [src: raw/project/snapshot-20261123d/crossings_worker.py#L3-L4] [src: raw/project/snapshot-20261123d/crossings_worker.json#key=amb_one_side] |
| corridor_cal_h_max | 地平線低於第 110 列的走廊現場校正拒收（坡上校正會讓彎 2 出口走廊偏左 110～120 px） | 110 | [src: raw/project/snapshot-20261123d/junction_corridor.py#L142-L145] [src: raw/project/snapshot-20261123d/crossings_worker.json#key=corridor_cal_h_max] |
| outside_handback（px 120、同側、歷史 3 格） | 走廊接手後若車跑到走廊外，可交還給連續、同側的基準路徑（彎 3） | true | [src: raw/project/snapshot-20261123d/crossings_worker.py#L9-L14] [src: raw/project/snapshot-20261123d/crossings_worker.json#key=outside_handback] |
| slope_width | worker IMU 俯仰 ≤ −8° 時，單線寬度比從 0.85 起並跟隨坡上看到的雙線比例 | pitch −8、ratio 0.85 | [src: raw/project/snapshot-20261123d/crossings_worker.py#L15-L17] [src: raw/project/snapshot-20261123d/crossings_worker.json#key=slope_width] |
| corridor_cal_gate | 地平線低於 110 px、寬度斜率 > 4.5 的走廊校正拒收；下坡時丟棄寬校正 | hmax 110、ws_max 4.5 | [src: raw/project/snapshot-20261123d/crossings_worker.json#key=corridor_cal_gate] |
| curve_take_guard | 轉彎中（|gz| ≥ 20 dps）、走廊弱側 < 25 列、走廊在彎外側且基準連續時，不准走廊以「不一致」接手，維持 0.6 s（彎 2 出彎） | gz_min 20、lr_max 25、hold 0.6 | [src: raw/project/snapshot-20261123d/crossings_worker.json#key=curve_take_guard] [src: raw/project/snapshot-20261123d/crossings_worker.json#key=note_curve_take_guard] |
| fallback_cont_px | fallback 接手的連續性限制 | null（關） | [src: raw/project/snapshot-20261123d/crossings_worker.json#key=fallback_cont_px] |

另外，`ground_identity`（最終版開啟）用地面座標比對上一格與本格的白線，分辨「自己車道的邊線」與「交叉線」（交叉線方向不同、另一條邊線遠 46 cm）[src: raw/project/snapshot-20261123d/ground_identity.py#L1-L8]，也是路口防抓錯線的一環。

### 最終實跑中的實際使用（run-b541）

由 tools/stats_vision_validity.py 自逐格紀錄 pid.jsonl（MANIFEST external 項）計算 [src: raw/records/runs/run-b541-20261123/summary.json]：

| 路段 | 格數 | 基準 baseline | 走廊 corridor | 走廊選定後無效格 |
|---|---|---|---|---|
| diagonal_v（02→03 斜線路口） | 419 | 300 | 119 | 0 [src: raw/records/runs/run-b541-20261123/summary.json] |
| circle_straight（04→05 圓圈直線） | 221 | 211 | 10 | 0 [src: raw/records/runs/run-b541-20261123/summary.json] |
| curve3（06～09） | 323 | 195 | 128 | 0 [src: raw/records/runs/run-b541-20261123/summary.json] |
| main_straight | 388 | 372 | 16 | 0 [src: raw/records/runs/run-b541-20261123/summary.json] |
| curve4 | 278 | 259 | 19 | 0 [src: raw/records/runs/run-b541-20261123/summary.json] |

兩個交叉路段在本輪都沒有出現走廊選定後的無效格。注意本輪 diagonal_v 中有 4 格基準本身無效、由走廊補上（同表的完整版見 [[path/vision-failure-modes]]）。

## 公式與參數

- 走廊模型：center(y) ＝ v_x + s·(y − y_h)；half(y) ＝ k·a·(y − y_h)/2（設計假設：平地、直線車道、固定地平線）[src: raw/project/snapshot-20261123d/junction_corridor.py#L5-L6]
- 預設校正 y_h ＝ 55.36 px、a ＝ 3.3058（多輪現場校正的量測值）[src: raw/project/snapshot-20261123d/junction_corridor_default.json#key=horizon_y] [src: raw/project/snapshot-20261123d/junction_corridor_default.json#key=width_slope]
- 切換參數 N 20 列、D 80 px、AGREE_PX 20、AGREE_DIR_PX 30、AGREE_FRAMES 3、PREDICT_S 0.4 s、STOP_S 0.4 s、GAP_S 0.4 s（實驗值，程式註明「不是安全限制」）[src: raw/project/snapshot-20261123d/junction_switch.py#L68-L69] [src: raw/project/snapshot-20261123d/junction_switch.py#L23-L24]；WEAK_S 2.0 s（現場調參）[src: raw/project/snapshot-20261123d/junction_live.py#L42]；DIR_TAKE_PX 70、DIR_TAKE_FRAMES 5（實驗值）[src: raw/project/snapshot-20261123d/junction_switch.py#L232]

## 未確認

- 走廊模型假設「直線車道」，在彎 3 這類彎道中走廊被大量採用（本輪 128／323 格），其路徑是否合乎彎道幾何，原始資料只以 outside_handback 等規則處理，未見專門評估。 [src: raw/records/runs/run-b541-20261123/summary.json]
- 路口處走廊接手前後的路徑跳動量（target_jump）本頁未統計。

## 相關條目

- [[path/mask-to-path]]、[[path/vision-failure-modes]]
- [[control/heading-hold]]（路口方向保持）、[[control/lost-path]]
- [[experiments/s-weave]]、[[experiments/failures-abandoned]]
