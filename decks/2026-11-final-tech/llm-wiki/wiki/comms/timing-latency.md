---
id: comms/timing-latency
title: 時序與延遲：控制資料年齡、推論耗時、命令頻率
status: implemented
sources:
  - raw/records/logs/AGENTS.md
  - raw/records/runs/run-b541-20261123/summary.json
  - raw/records/analyses/a1-poster-factcheck-20261103.md
  - raw/records/analyses/why-s-weave-20261107-findings.json
  - raw/project/imu-new-20261105/imu_logger.py
  - raw/project/snapshot-20261123d/imu_boost.json
  - raw/project/snapshot-20261123d/uart_nonblock.json
  - raw/project/snapshot-20261123d/_extra/start_params.json
  - raw/project/firmware-pwm100_v1/Config.h
  - raw/project/docs/PROTOCOL.md
verified_against: snapshot-20261123d
updated: 2026-11-23
---

# 時序與延遲：控制資料年齡、推論耗時、命令頻率

## 一句話結論

最終版相機約 30 張/s，Orin 上每格推論＋路徑計算中位數 57.4 ms，控制迴圈實際每秒消費約 23.4 格（約 78% 的相機影格），影像從擷取到被 PID 使用的「控制資料年齡」中位數 87.4 ms、P95 112.0 ms；再加上舵機與車身反應，命令到車頭轉向約 0.24～0.30 s（由 tools/stats_timing.py 自逐格紀錄 pid.jsonl（MANIFEST external 項）計算）[src: raw/records/runs/run-b541-20261123/summary.json] [src: raw/records/logs/AGENTS.md#L108]。

## 內容

### 三段時間要分開看

專案規則要求延遲分三段記錄，不能混為一談 [src: raw/records/logs/AGENTS.md#L48-L50]：

1. **控制資料年齡**：Orin 相機擷取 → 辨識／路徑 → PID 消費。這段才影響控制 [src: raw/records/logs/AGENTS.md#L48]。
2. **觀測延遲**：Orin 結果 → 網路 → 筆電畫面。筆電畫面慢不代表車上控制用的是舊影像 [src: raw/records/logs/AGENTS.md#L49]。
3. **指令延遲**：筆電按開始／停止 → Orin 接受回覆 [src: raw/records/logs/AGENTS.md#L48]。

此外：查詢時的 latest.age_s 不等於該影格當初被 PID 消費時的年齡；推論耗時也不等於端到端控制延遲；不同機器時鐘未對齊時不能直接相減 [src: raw/records/logs/AGENTS.md#L50]。本頁的數字都屬第 1 段，且只用同一台 Orin 的單調時鐘。`orin_timed` 模式下 Orin 接受開始後獨立完成本輪，筆電斷線不會中止 [src: raw/records/logs/AGENTS.md#L52]；最終實跑即此模式 [src: raw/records/runs/run-b541-20261123/summary.json#L36]。

### 最終版實測（run-b541，11-23 定版輪）

以下數字由 `tools/stats_timing.py` 自 run-b541 的逐格紀錄 pid.jsonl（MANIFEST external 項，55 MB，不複製進 raw）計算；該輪摘要見 [src: raw/records/runs/run-b541-20261123/summary.json]。只計 kind 為 sample 的列（每列＝一次送出的命令，2804 列，wall 時間跨度 119.8 s）[src: raw/records/runs/run-b541-20261123/summary.json]。

| 項目 | 中位數 | 第九十五百分位 | 最小～最大 | 出處 |
|---|---|---|---|---|
| 推論耗時 vision.inference_ms | 57.4 ms | 71.9 ms | 37.2～96.3 ms | [src: raw/records/runs/run-b541-20261123/summary.json] |
| 其中：模型 stage_ms.model | 20.2 ms | 25.8 ms | 18.5～50.1 ms | [src: raw/records/runs/run-b541-20261123/summary.json] |
| 其中：路徑計算 stage_ms.path | 33.0 ms | 41.7 ms | 14.8～61.6 ms | [src: raw/records/runs/run-b541-20261123/summary.json] |
| 其中：解碼 stage_ms.decode | 1.8 ms | 4.5 ms | 1.4～17.5 ms | [src: raw/records/runs/run-b541-20261123/summary.json] |
| 其中：佇列 stage_ms.queue | 0.4 ms | 8.2 ms | 0.1～30.1 ms | [src: raw/records/runs/run-b541-20261123/summary.json] |
| 控制資料年齡（consumed_at−capture_at） | 87.4 ms | 112.0 ms | 55.2～160.7 ms | [src: raw/records/runs/run-b541-20261123/summary.json] |
| PID 相鄰兩格間隔（wall） | 40.9 ms | 63.9 ms | 11.3～106.3 ms | [src: raw/records/runs/run-b541-20261123/summary.json] |

- 每秒命令數＝每秒新影格數＝23.41（2804÷119.8，推算）[src: raw/records/runs/run-b541-20261123/summary.json]。
- 相機 frame_seq 在 119.8 s 內前進 3571，擷取約 29.82 張/s；PID 消費的影格約占 0.78，其餘被較新的影格取代而跳過 [src: raw/records/runs/run-b541-20261123/summary.json]。
- 各階段中位數相加約 55.4 ms（1.8＋20.2＋33.0＋0.4，推算），接近 inference_ms 中位數，推論該欄位涵蓋 worker 一格的總處理時間，而不只是模型本身 [src: raw/records/runs/run-b541-20261123/summary.json]。
- 摘要中最後一格的 capture／consumed 時間差為 0.092 s（1686.105−1686.013，推算），與上述分布一致 [src: raw/records/runs/run-b541-20261123/summary.json#L45-L46]。

### 紀錄中的經驗值

- 相機固定手動曝光 30 ms＋gamma 300，約 30 張/s [src: raw/records/logs/AGENTS.md#L100]。
- worker 每格約 49～55 ms、全場約 30 張/s、影像年齡中位約 60～85 ms [src: raw/records/logs/AGENTS.md#L114]。run-b541 的推論耗時 57.4 ms 與控制資料年齡 87.4 ms 都略高於這個範圍的上緣；兩者量的是不同輪次，紀錄中的範圍未註明計算方式。
- 指令→車頭延遲約 0.24～0.30 s，與每秒張數無關 [src: raw/records/logs/AGENTS.md#L108]。

### 其他環節的時間常數

| 環節 | 數值 | 出處 |
|---|---|---|
| IMU 紀錄程序取樣率（預設） | 50 Hz | [src: raw/project/imu-new-20261105/imu_logger.py#L67] |
| 控制端接受的 IMU 資料最大年齡 | 0.3 s | [src: raw/project/snapshot-20261123d/imu_boost.json#key=max_age_s] |
| PID 判定影像過舊（max_gap） | 0.4 s | [src: raw/project/snapshot-20261123d/_extra/start_params.json#L44] |
| UART move 送出間隔 | 0.025～0.1 s | [src: raw/project/snapshot-20261123d/uart_nonblock.json] |
| UART 最多未確認筆數／連線遺失判定 | 2 筆／0.45 s | [src: raw/project/snapshot-20261123d/uart_nonblock.json] |
| 控制板狀態（含編碼器）回報週期 | 200 ms | [src: raw/project/firmware-pwm100_v1/Config.h#L40] |
| 控制板命令租期 | 500 ms | [src: raw/project/firmware-pwm100_v1/Config.h#L35] |
| 控制板舵機追蹤速率 | 40 µs／20 ms | [src: raw/project/firmware-pwm100_v1/Config.h#L38-L39] |

UART 細節見 [[comms/uart-protocol]]；各層如何使用這些時間（例如遺失判定）見 [[control/command-chain]]。

### 早期版本對照（11-02～11-03，只作對照）

11-03 的海報查核文件記錄 11-02 一輪（1129 格，PyTorch FP32、未用 TensorRT）：模型推論中位數 26 ms／P95 32 ms、推論＋路徑 94／110 ms、取像到控制採用 132／170 ms，控制更新約每秒 10 次 [src: raw/records/analyses/a1-poster-factcheck-20261103.md#L52-L61]。與最終版相比，路徑計算與管線重疊的改進使控制頻率由約 10 次/s 提高到約 23 次/s、資料年齡由 132 ms 降到 87 ms（兩個不同輪次的比較，非同條件實驗）。

### 迴路延遲的兩個估計

- 11-07 的 S 型分析估計：相機→PID 0.12 s（P95 0.16）、PID→控制板 0.1 s、命令→偏航反應 0.5～0.6 s，合計約 0.75 s 迴路延遲 [src: raw/records/analyses/why-s-weave-20261107-findings.json#L12]。
- 之後的紀錄則寫指令→車頭延遲約 0.24～0.30 s [src: raw/records/logs/AGENTS.md#L108]。兩者之間韌體舵機追蹤速率在 11-08 由 1000 µs/s 提高到 2000 µs/s [src: raw/project/firmware-pwm100_v1/Config.h#L39]；差異是否全部來自此變更、或兩者定義不同（相關峰值 vs 擬合延遲），來源無法判定，已列入衝突草稿。S 型擺動與延遲的關係見 [[control/yaw-inner]]。

## 公式與參數

```
控制資料年齡 = vision.consumed_at − vision.capture_at        （同一台 Orin 的 monotonic 時鐘）
每秒命令數   = sample 列數 / (最後 wall − 第一 wall)
相機張數/s   ≈ (frame_seq_末 − frame_seq_首) / (capture_at_末 − capture_at_首)
```
[src: raw/records/runs/run-b541-20261123/summary.json#L45-L46]

| 參數 | 值 | 性質 | 出處 |
|---|---|---|---|
| 相機曝光 | 30 ms（手動） | 調參值 | [src: raw/records/logs/AGENTS.md#L100] |
| 相機擷取速率 | 29.82 張/s | 實測值（run-b541） | [src: raw/records/runs/run-b541-20261123/summary.json] |
| 推論耗時中位數／P95 | 57.4／71.9 ms | 實測值（run-b541） | [src: raw/records/runs/run-b541-20261123/summary.json] |
| 控制資料年齡中位數／P95 | 87.4／112.0 ms | 實測值（run-b541） | [src: raw/records/runs/run-b541-20261123/summary.json] |
| 控制頻率 | 23.41 格/s | 實測值（run-b541） | [src: raw/records/runs/run-b541-20261123/summary.json] |
| 指令→車頭延遲 | 0.24～0.30 s | 實測值（擬合） | [src: raw/records/logs/AGENTS.md#L108] |
| IMU 取樣率 | 50 Hz | 設計假設（程式預設值） | [src: raw/project/imu-new-20261105/imu_logger.py#L67] |

## 未確認

- 統計只涵蓋 run-b541 一輪（約 2 圈、119.8 s）；不同路段（上層、坡道）的延遲分布未分開計算 [src: raw/records/runs/run-b541-20261123/summary.json]。
- 「PID 消費→控制板收到命令→舵機實際到位」這段沒有逐格時間戳；ACK 只代表接受 [src: raw/project/docs/PROTOCOL.md#L68]。
- IMU 紀錄程序實際取樣率（是否以 50 Hz 執行、有無掉樣）未從 IMU 紀錄檔統計 [src: raw/project/imu-new-20261105/imu_logger.py#L67]。
- 0.24～0.30 s 與 0.5～0.6 s 兩個延遲估計的定義差異未釐清 [src: raw/records/logs/AGENTS.md#L108] [src: raw/records/analyses/why-s-weave-20261107-findings.json#L12]。

## 相關條目

- [[comms/uart-protocol]]
- [[control/command-chain]]
- [[control/yaw-inner]]
- [[control/lap-position]]
- [[path/vision-failure-modes]]
- [[hardware/imu-mpu6050]]
- [[experiments/final-performance]]
- [[overview]]
