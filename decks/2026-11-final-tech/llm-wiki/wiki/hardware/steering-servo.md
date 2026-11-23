---
id: hardware/steering-servo
title: 轉向舵機、保存設定與轉向量測事實
status: implemented
sources:
  - raw/project/snapshot-20261123d/_extra/servo_profile.json
  - raw/project/snapshot-20261123d/_extra/start_params.json
  - raw/project/snapshot-20261123d/play_comp.json
  - raw/project/firmware-pwm100_v1/Config.h
  - raw/project/firmware-pwm100_v1/Drive.cpp
  - raw/project/docs/Orin_Interface_v1-README.md
  - raw/records/runs/run-b541-20261123/summary.json
  - raw/records/logs/AGENTS.md
  - raw/records/logs/AGENTS_LOG_202611.md
verified_against: snapshot-20261123d
updated: 2026-11-23
---

# 轉向舵機、保存設定與轉向量測事實

## 一句話結論

前輪由一顆舵機經連桿轉向，舵機脈波由 PCA9685 的 CH0 以 50 Hz 輸出；最終版保存設定 rev44 為最小 780 µs／中心 1445 µs／最大 2050 µs [src: raw/project/snapshot-20261123d/_extra/servo_profile.json#key=center_us] [src: raw/project/firmware-pwm100_v1/Drive.cpp#L184]。11-23 舊舵機損壞後換上新舵機，新舵機量到直行點約 1443、間隙約 60 µs、增益約 0.19 deg/m per µs，與舊舵機數字不同，舊數字不再適用 [src: raw/records/logs/AGENTS.md#L151] [src: raw/records/logs/AGENTS_LOG_202611.md#L1646]。

## 內容

### 名詞

- **舵機脈寬（µs）**：舵機每 20 ms（50 Hz）收到一個脈波，脈波越寬轉得越多；本車「數字大＝往右」[src: raw/records/logs/AGENTS_LOG_202611.md#L1632]。
- **共用中心（center_us）**：控制程式當作「方向盤回正」的脈寬；全車只有一個中心，改值時各層一起變 [src: raw/records/logs/AGENTS.md#L151]。
- **直行點**：實際讓車走直線的脈寬，由實跑資料擬合（工具 play_now）[src: raw/records/logs/AGENTS_LOG_202611.md#L1646]。
- **間隙（backlash）**：舵機換方向時，連桿有一段「舵機在轉、輪子還沒動」的空行程，以 µs 表示 [src: raw/records/logs/AGENTS.md#L108]。軟體補償的做法見 [[control/play-comp]]。

### 硬體路徑

Orin 送出轉向目標 → UART → BMduino 控制板 → I²C → PCA9685 CH0（位址 0x40）→ 舵機 → 連桿 → 前輪 [src: raw/project/firmware-pwm100_v1/Config.h#L15] [src: raw/project/firmware-pwm100_v1/Drive.cpp#L183-L184]。

- PCA9685 開機時先關 CH0、設定振盪器與 50 Hz，再關一次輸出，之後才回中 [src: raw/project/firmware-pwm100_v1/Drive.cpp#L180-L186]；開機中心策略為「先關舵機輸出，收到 Orin 保存設定後回中一次」[src: raw/records/logs/AGENTS.md#L120]。
- 韌體在 MANUAL 狀態（控制板接受 Orin 轉向目標的狀態）下，每 20 ms 最多移動 40 µs，即 2000 µs/s 的轉向速率上限（註解：原為 1000 µs/s）[src: raw/project/firmware-pwm100_v1/Drive.cpp#L314-L319] [src: raw/project/firmware-pwm100_v1/Config.h#L38]。Orin 端起跑參數另設 `steer_rate` 1500（µs/s）[src: raw/project/snapshot-20261123d/_extra/start_params.json#key=start.parameters.steer_rate]。
- 韌體端的命令包絡 500／1500／2500 µs 是「TD-8135MG」的範圍，連桿極限要在其內另行校正 [src: raw/project/firmware-pwm100_v1/Config.h#L26-L27]；實際限幅以保存設定（780／1445／2050）為準 [src: raw/project/snapshot-20261123d/_extra/servo_profile.json]。

### 最終版設定（rev44）

| 項目 | 值 | 性質 | 依據 |
|---|---|---|---|
| 最小 min_us | 780 | 實測校正值（連桿極限） | [src: raw/project/snapshot-20261123d/_extra/servo_profile.json#key=min_us] |
| 中心 center_us | 1445 | 依新舵機實跑擬合的直行點設定 | [src: raw/project/snapshot-20261123d/_extra/servo_profile.json#key=center_us] |
| 最大 max_us | 2050 | 實測校正值（連桿極限） | [src: raw/project/snapshot-20261123d/_extra/servo_profile.json#key=max_us] |
| 間隙補償左右 | ±15 µs，門檻 15 µs | 調參值 | [src: raw/project/snapshot-20261123d/play_comp.json#key=right_us] [src: raw/project/snapshot-20261123d/play_comp.json#key=threshold_us] |
| 左右增益 left_gain／right_gain | 1.5／1.45 | 調參值 | [src: raw/project/snapshot-20261123d/_extra/start_params.json#key=start.parameters.left_gain] |

最終實跑 run-b541 的紀錄也顯示 limits revision 44、780／1445／2050 [src: raw/records/runs/run-b541-20261123/summary.json#L16-L21]。右行程 1445→2050 為 605 µs、左行程 1445→780 為 665 µs [src: raw/records/logs/AGENTS_LOG_202611.md#L1652]。

`play_comp.json` 內的備註仍寫 55→25，那是 16:46 的修改紀錄；之後 17:19 再改成 ±15 並實跑 [src: raw/records/logs/AGENTS.md#L143-L144]，以檔內數值 15 為準 [src: raw/project/snapshot-20261123d/play_comp.json#key=right_us]。

### 11-23 換舵機經過

1. 15:04 run-4abf 撞隧道，事後判定是舵機故障、轉向沒照指令動；16:34 使用者換上新舵機，全車油門上限暫降為 50 [src: raw/records/logs/AGENTS.md#L153]。
2. 新舵機第一圈（run-b3ab）：直行點約 1435（當時中心 1475 偏右約 40）、間隙約 60（原 130）、增益 0.184；直線要一直往左壓 25～30 µs [src: raw/records/logs/AGENTS_LOG_202611.md#L1639-L1640]。
3. 三輪 play_now 一致：直行點 1435／1442／1444、間隙 60、增益 0.184／0.195／0.194（舊舵機 0.172）、延遲 0.26 s（舊 0.20）[src: raw/records/logs/AGENTS_LOG_202611.md#L1646]。
4. 16:46 中心 1475→1445（保存設定 rev43→44）、補償 ±55→±25 [src: raw/records/logs/AGENTS_LOG_202611.md#L1652] [src: raw/records/logs/AGENTS_LOG_202611.md#L1655]；改後兩輪直行點 1445／1448、間隙 60、增益 0.193／0.201、延遲 0.20，直線擺動約減半 [src: raw/records/logs/AGENTS_LOG_202611.md#L1661-L1662]。
5. 17:19 補償再降為 ±15，run-ce19 直線 gz 標準差 6.1～7.0（改前 7.6～9.5）[src: raw/records/logs/AGENTS.md#L143]。
6. 未處理：新舵機增益比舊的高約 10%，各彎帶狀舵量表仍是舊舵機時代調的 [src: raw/records/logs/AGENTS_LOG_202611.md#L1658]。

### 舊舵機時代的量測（僅供對照，不適用於最終版）

- 11-12 地墊實測遲滯約 155 µs、增益約 0.32 deg/m per µs（0.37 m/s）；跑圈擬合間隙約 110～130 µs、增益約 0.16～0.20；指令→車頭延遲約 0.24～0.30 s，與每秒張數無關 [src: raw/records/logs/AGENTS.md#L108]。
- 鎖緊間隙時補償要同步調小或關；模型估計只鎖緊不改補償，擺幅約 2～2.6 倍 [src: raw/records/logs/AGENTS.md#L108]。

## 公式與參數

- 舵機轉角與車子轉彎的關係，以「增益」描述（實測擬合值）：
  曲率變化（deg/m）≈ 增益 × （實送脈寬 − 直行點）（µs）
  - 新舵機增益 0.184～0.201（實測，play_now 擬合）[src: raw/records/logs/AGENTS_LOG_202611.md#L1646] [src: raw/records/logs/AGENTS_LOG_202611.md#L1661]
  - 直行點 1435～1448（實測）[src: raw/records/logs/AGENTS_LOG_202611.md#L1646] [src: raw/records/logs/AGENTS_LOG_202611.md#L1661]
- 轉向速率上限：韌體 40 µs／20 ms ＝ 2000 µs/s（設計值）[src: raw/project/firmware-pwm100_v1/Drive.cpp#L317]；起跑參數 steer_rate 1500 µs/s（調參值）[src: raw/project/snapshot-20261123d/_extra/start_params.json#key=start.parameters.steer_rate]
- 推算：50 Hz 的脈波週期 ＝ 1 ÷ 50 ＝ 20 ms（推算）。 [src: raw/project/firmware-pwm100_v1/Drive.cpp#L184]

## 未確認

- 新舵機型號原始資料未記載。Config.h 註解的 TD-8135MG 是韌體命令包絡的依據 [src: raw/project/firmware-pwm100_v1/Config.h#L26]，不能據此說新舵機也是 TD-8135MG。
- 指令→車頭延遲：AGENTS.md 舊舵機記為 0.24～0.30 s [src: raw/records/logs/AGENTS.md#L108]，11-23 紀錄寫「舊 0.20」[src: raw/records/logs/AGENTS_LOG_202611.md#L1646]，新舵機兩次量到 0.26 與 0.20 s [src: raw/records/logs/AGENTS_LOG_202611.md#L1646] [src: raw/records/logs/AGENTS_LOG_202611.md#L1661]。量法可能不同（未確認），已記入衝突草稿。
- README 的「CH0、50 Hz，中心 1340 µs，範圍 ±700 µs」是 10 月第一版 [src: raw/project/docs/Orin_Interface_v1-README.md#L52]，與最終版不同；以保存設定為準。

## 相關條目

- [[control/play-comp]]（間隙補償）、[[control/command-chain]]（命令如何算出與限幅）、[[control/pid-core]]
- [[comms/uart-protocol]]、[[hardware/vehicle-hardware]]
- [[experiments/failures-abandoned]]、[[experiments/final-performance]]
