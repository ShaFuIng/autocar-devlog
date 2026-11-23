---
id: experiments/final-performance
title: 最終版（快照 20261123d）的實測表現
status: implemented
sources:
  - raw/project/snapshot-20261123d/README.md
  - raw/records/runs/run-b541-20261123/summary.json
  - raw/records/logs/AGENTS.md
  - raw/records/logs/AGENTS_LOG_202611.md
  - raw/records/logs/AGENTS_HISTORY_until_20261119.md
  - raw/project/snapshot-20261123d/throttle_cap.json
  - raw/project/snapshot-20261123d/play_comp.json
  - raw/project/snapshot-20261123d/lap_speed.json
verified_against: snapshot-20261123d
updated: 2026-11-23
---

# 最終版（快照 20261123d）的實測表現

## 一句話結論

使用者 11-23 18:1x 定版的最終版只正式跑過一輪 run-b541，兩個計時圈 56.5／56.8 s、無失敗；同一天的最快單圈 55.4 s 是舵機故障更換前、設定也不同的 run-9729，兩者不可混為「最終版成績」[src: raw/project/snapshot-20261123d/README.md#L1-L4] [src: raw/records/logs/AGENTS_LOG_202611.md#L1603]。

## 內容

- 【使用者 11-23 決定，見 [[conflicts]] D1】對外一律以 run-b541 的 56.5 s 為最終版成績，並標明是「賽前實測」，不是正式比賽成績；55.4 s 只在歷史演進中提及並註明舊舵機 [src: raw/project/snapshot-20261123d/README.md#L4]。

### 名詞

- **快照**：把車上 Orin 控制程式資料夾整份複製下來、逐檔核對雜湊的存檔；「最終版」＝快照 20261123d [src: raw/project/snapshot-20261123d/README.md#L1-L3]。
- **run 編號**：每一次開跑（一輪）的編號取前四碼；一輪可含多圈。
- **計時圈**：本頁 11-23 的圈速以「各段加總」計（紀錄寫法），手動停止那一圈另算規則見 [[experiments/lap-progression]] [src: raw/records/logs/AGENTS_LOG_202611.md#L1452]。
- **效能比**：比賽計分項之一，＝平均車速 ÷ 最高車速；本車最高速以落地油門 100% 實測約 1.44 m/s 為準 [src: raw/records/logs/AGENTS.md#L127]。

### 最終版是什麼

- 快照 20261123d＝車上控制程式資料夾最上層 201 檔（逐檔核對相同）＋舵機保存設定 rev44（780／1445／2050）與手機起跑參數；油門上限 100、起點＝旗子位置 [src: raw/project/snapshot-20261123d/README.md#L3]。
- 相對前一份快照 20261123c 只差兩個設定檔：彎 2 入彎前段的帶狀曲率調小（kappa_turn 0°32→30、30°36→33.5），以及坡道油門 100 區加逐區誤差門檻 err_guard 0.4、油門上升速率 70 PWM/s [src: raw/project/snapshot-20261123d/README.md#L5-L7] [src: raw/project/snapshot-20261123d/lap_speed.json#L65-L70]。
- 新舵機設定：共用中心 1445、間隙補償 ±15、虛線轉彎位置備援 2.5 m [src: raw/project/snapshot-20261123d/README.md#L8] [src: raw/project/snapshot-20261123d/play_comp.json#L3-L5]。油門上限檔為 100 [src: raw/project/snapshot-20261123d/throttle_cap.json]。
- 使用者原話「就用這版本了不改了」[src: raw/records/logs/AGENTS_LOG_202611.md#L1734]。

### run-b541（最終版唯一一輪，實車）

| 項目 | 數值 | 出處 |
|---|---|---|
| 計時圈 | 56.5／56.8 s，無失敗 | [src: raw/records/logs/AGENTS_LOG_202611.md#L1730] |
| 上坡時間 | 2.97／2.88 s | [src: raw/records/logs/AGENTS_LOG_202611.md#L1731] |
| 上坡油門 ≥90 的格數 | 6／3 格 | [src: raw/records/logs/AGENTS_LOG_202611.md#L1731] |
| 坡道後段 gz 標準差 | 20／21 | [src: raw/records/logs/AGENTS_LOG_202611.md#L1731] |
| 坡道後段誤差擺幅 | 0.60／0.62 | [src: raw/records/logs/AGENTS_LOG_202611.md#L1731] |
| 虛線轉彎 | 2/2 轉完，起轉 TOP+2.57／2.62 m | [src: raw/records/logs/AGENTS_LOG_202611.md#L1731] |
| 彎 2 內線／外線淨空 | −3.6／−7.1 cm；+8.2／+9.0 cm | [src: raw/records/logs/AGENTS_LOG_202611.md#L1731] |

- 結束原因 USER_STOP（使用者停止）、執行模式 orin_timed、舵機中心 1445、舵機設定 rev 44 [src: raw/records/runs/run-b541-20261123/summary.json#L5] [src: raw/records/runs/run-b541-20261123/summary.json#L11] [src: raw/records/runs/run-b541-20261123/summary.json#L16-L21] [src: raw/records/runs/run-b541-20261123/summary.json#L36]。
- summary.json 本身不含圈速；圈速取自紀錄檔 [src: raw/records/runs/run-b541-20261123/summary.json]。
- 坡道數字與門檻 0.5 時相近，紀錄註明「樣本 2 次」[src: raw/records/logs/AGENTS_LOG_202611.md#L1731]。

### 同日新舵機時期各輪（實車）

11-23 15:04 舵機故障撞隧道，16:34 換新舵機，之後以下各輪皆為新舵機 [src: raw/records/logs/AGENTS_LOG_202611.md#L1631-L1632]。

| 時間 | run | 油門上限／主要設定 | 計時圈（s） | 失敗 | 出處 |
|---|---|---|---|---|---|
| 16:38 | b3ab | 上限 50，中心 1475 | 61.7 | 無 | [src: raw/records/logs/AGENTS_LOG_202611.md#L1638] |
| 16:4x | 6855 | 上限 50 | 60.6／59.9 | 無 | [src: raw/records/logs/AGENTS_LOG_202611.md#L1645] |
| 17:0x | a216／ec90 | 上限 50，中心 1445 | 61.0／60.0 | 無 | [src: raw/records/logs/AGENTS_LOG_202611.md#L1669] |
| 17:1x | 2395 | 上限 50，位置備援 2.65 | 59.9／60.5／60.4 | 無 | [src: raw/records/logs/AGENTS_LOG_202611.md#L1679] |
| 17:2x | 21fe／8ce6 | 上限 100 | 57.3／56.6；56.7 | 無 | [src: raw/records/logs/AGENTS_LOG_202611.md#L1688] |
| 17:2x | ce19 | 位置備援 2.5＋補償 ±15 | 56.1／57.2（第 3 圈手動停不計） | 無 | [src: raw/records/logs/AGENTS_LOG_202611.md#L1697] |
| 17:3x | 5f69 | 同上（存快照 20261123c） | 56.3／56.6／57.2／56.0 | 無 | [src: raw/records/logs/AGENTS_LOG_202611.md#L1703] |
| 17:4x | ed3d／cb0f | 彎 2 入彎調小 | 57.0／56.3；57.4／56.4 | 無 | [src: raw/records/logs/AGENTS_LOG_202611.md#L1712] |
| 18:0x | 9dba 等四輪 | 坡道 err_guard 0.5 | 9dba 56.4／56.4（其他三輪未列圈速） | 無 | [src: raw/records/logs/AGENTS_LOG_202611.md#L1721] |
| 18:1x | b541 | 坡道 err_guard 0.4（＝最終版） | 56.5／56.8 | 無 | [src: raw/records/logs/AGENTS_LOG_202611.md#L1730] |

- 新舵機時期最快的單一計時圈是 run-5f69 的 56.0 s（快照 20261123c，比最終版少兩檔改動），不是最終版的 56.5 s [src: raw/records/logs/AGENTS_LOG_202611.md#L1703]。
- 換新舵機後到定版，紀錄中各輪皆無失敗 [src: raw/records/logs/AGENTS_LOG_202611.md#L1638-L1734]。

### 換舵機前的同日最快（舊舵機，設定不同）

- run-9729（14:5x）6 圈 56.5／56.4／56.0／57.7／55.7／55.4 s、無失敗，55.4 為當時最快 [src: raw/records/logs/AGENTS_LOG_202611.md#L1603]。
- run-d380（14:3x）5 圈中最快 55.7 s [src: raw/records/logs/AGENTS_LOG_202611.md#L1584]。
- 下一輪 run-4abf（同設定）第 1 圈撞隧道，原因後來由使用者確認為舵機故障 [src: raw/records/logs/AGENTS_LOG_202611.md#L1622-L1632]。
- 新舵機全速圈比舊舵機最佳慢：紀錄寫「新舵機全速圈時回到 56.6～57.3 s（舊舵機最佳 55.4～56.5）」[src: raw/records/logs/AGENTS_LOG_202611.md#L1689]。
- **封面要用哪個數字由人決定**，見衝突草稿「封面成績」。

### 效能比

- 有紀錄的：run-5b69（11-23 上午，舊舵機）「效能比約 67.6 m÷56.5 s÷1.44＝83%」[src: raw/records/logs/AGENTS_LOG_202611.md#L1452]。
- 最終版 run-b541 **沒有**效能比紀錄 [src: raw/records/logs/AGENTS_LOG_202611.md#L1730-L1734]。
- 【使用者 11-23 決定採用，見 [[conflicts]] D2】推算：沿用 run-5b69 同一算法，67.6 m ÷ 56.5 s ÷ 1.44 m/s ≈ 0.831，即約 83%；用第二圈 56.8 s 則 67.6 ÷ 56.8 ÷ 1.44 ≈ 0.826 [src: raw/records/logs/AGENTS_LOG_202611.md#L1452] [src: raw/records/logs/AGENTS_LOG_202611.md#L1730]。
- 圈長的紀錄值不只一個：11-13 量測「一圈 67.71±0.24 m」、11-22「圈長 67.5～67.7 m」、11-20 計算用 67.1 m [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L403] [src: raw/records/logs/AGENTS_LOG_202611.md#L1401] [src: raw/records/logs/AGENTS_LOG_202611.md#L334]。以 67.71 m 推算為 67.71 ÷ 56.5 ÷ 1.44 ≈ 0.832（推算）。

### 定版時已知未處理

- 坡腳回擺變大（上坡略晃）、比賽起跑模式未驗、需重啟的候選未上車 [src: raw/records/logs/AGENTS.md#L136]。
- Orin 在 17:45 重開機過，之後 IMU 靜止值未核對（各輪坡道與地標辨識正常）[src: raw/records/logs/AGENTS_LOG_202611.md#L1733]。
- 上坡變慢的原因已查到是新舵機坡腳回擺過頭使坡道 100 區被誤差門檻擋住；放寬門檻後上坡變快但擺動變大，根因未處理 [src: raw/records/logs/AGENTS_LOG_202611.md#L1714-L1716] [src: raw/records/logs/AGENTS_LOG_202611.md#L1722-L1725]。

### 辨識表現

- 模型辨識指標（例如邊界 IoU）屬感知，不在本頁；見 [[perception/yolo26-sem]]。

## 公式與參數

- 效能比（紀錄的算法）＝圈長 ÷ 圈時間 ÷ 最高速 1.44 m/s [src: raw/records/logs/AGENTS_LOG_202611.md#L1452]；1.44 m/s 為落地油門 100% 的實測值（6492 cps）[src: raw/records/logs/AGENTS.md#L127]。
- 最終版推算值見上節，屬推算，不是實測紀錄。

## 未確認

- 最終版只有 run-b541 一輪、兩個計時圈；沒有重複輪可看分布 [src: raw/records/logs/AGENTS_LOG_202611.md#L1730]。
- run-b541 的逐段時間（各彎、各直線）紀錄未列 [src: raw/records/logs/AGENTS_LOG_202611.md#L1730-L1734]。
- 18:0x 四輪中 486f、6373、1a2f 的圈速紀錄未列 [src: raw/records/logs/AGENTS_LOG_202611.md#L1721]。
- 效能比推算所用圈長（67.6 m）是 11-23 上午的值，最終版沒有另量 [src: raw/records/logs/AGENTS_LOG_202611.md#L1452]。
- 定版後比賽當天的實際成績不在 raw 內。

## 相關條目

- [[experiments/lap-progression]]：圈速演進時間線。
- [[experiments/s-weave]]：新舵機時期直線擺動數字。
- [[hardware/steering-servo]]：舵機更換與中心、間隙。
- [[control/speed-control]]：油門區與坡道 err_guard。
- [[control/play-comp]]：間隙補償 ±15。
- [[perception/yolo26-sem]]：辨識指標。
- [[overview]]
