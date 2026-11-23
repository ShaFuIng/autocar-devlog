---
id: experiments/lap-progression
title: 圈速演進時間線（11-07 109.9 s → 11-23 56.5 s）
status: used-before
sources:
  - raw/records/logs/AGENTS.md
  - raw/records/logs/AGENTS_LOG_202611.md
  - raw/records/logs/AGENTS_HISTORY_until_20261119.md
  - raw/project/snapshot-20261123d/README.md
verified_against: snapshot-20261123d
updated: 2026-11-23
---

# 圈速演進時間線

## 一句話結論

有紀錄的單圈由 11-07 run-7fbf 的 109.9 s 一路降到 11-23 舊舵機 run-9729 的 55.4 s，最終定版 run-b541 為 56.5／56.8 s；中間每一點都只代表「當天那一輪」，各階段的計時定義、相機姿態與硬體並不完全相同，因此本頁只列有紀錄的改變，不把圈速差直接歸因給單一改動 [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L14] [src: raw/records/logs/AGENTS_LOG_202611.md#L1603] [src: raw/records/logs/AGENTS_LOG_202611.md#L1730]。

## 內容

### 讀表前須知

- **計時定義會變**：早期寫「完整一圈（彎 1 入→彎 1 入）」，11-18～11-19 寫「彎 1 計圈」，11-23 寫「各段加總」[src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L367] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L679] [src: raw/records/logs/AGENTS_LOG_202611.md#L1452]。手動停止的輪次「圈數＝彎 1 計時圈數＋1」[src: raw/records/logs/AGENTS.md#L102]。
- **地標代號**：C1s／C1e＝彎 1 起點／終點，C2e＝彎 2 終點，依此類推；彎道編號以統一跑道地圖為準（彎 1＝01～02、彎 2＝03～04、彎 3＝06～09、彎 4＝11～12）[src: raw/records/logs/AGENTS.md#L7]。
- **原始逐格紀錄**：筆電上 11-10 以前的原始紀錄已刪，只剩文字結論 [src: raw/records/logs/AGENTS.md#L375]。
- 「效能比」定義見 [[experiments/final-performance]]。

### 時間線（實車）

| 日期 | run | 單圈（s） | 備註 | 出處 |
|---|---|---|---|---|
| 11-07 13:45 | 7fbf | 109.9 | 兩圈；舊韌體轉向約 1000 µs/s 時期，後來保存為「慢速轉向版」方案 | [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L14] |
| 11-08 16:58 | 46db | 93.0 | 兩圈；「今日最佳版」 | [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L15] |
| 11-08 19:51 | 97ed | 96.3 | 兩圈 | [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L16] |
| 11-11 | cba7 | 87.9 | 完整一圈 | [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L367] |
| 11-11 19:57 | 6430 | 85.8 | 第二圈彎 1 後失敗；**19:40 後車上零件被踢到、相機姿態不可靠** | [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L17] |
| 11-12 | 676e | 81.9 | 間隙補償 ±55 首輪；相機不在標定姿態；第 2 圈出界 | [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L367] |
| 11-13 14:1x | 763c | 82.18～82.80 | 中心 1480，5 個完整圈＝當時新基準 | [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L388] |
| 11-13 16:4x | 4e63 | 81.98～83.49 | 5 個完整圈無失敗 | [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L400] |
| 11-14 16:02 | 51a0 | 76.7～78.3 | 定位 lap_pos 首次實車（只記錄） | [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L434] |
| 11-17 16:1x | 7afb | 71.0 | 間隙補償門檻 15 首輪 | [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L609] |
| 11-18 17:30 | 6c1e | 68.6～70.2（彎 1 計圈） | 內迴圈增益 k 6→4 首輪 | [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L660] |
| 11-18 19:3x | 973e | 66.2～69.4（彎 1 計圈） | 虛線相對白色門檻首輪 | [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L679] |
| 11-19 | a674 | 64.8～66.6（彎 1 計圈） | 4 圈無失敗 | [src: raw/records/logs/AGENTS.md#L326] |
| 11-19 19:3x | d2c7 | 65.4～66.8 | 「穩定版」，使用者認可 | [src: raw/records/logs/AGENTS.md#L324] |
| 11-19 20:38 | dc2b | 64.0／63.2（彎 1 計圈） | 三直線加長油門 100 等（runA） | [src: raw/records/logs/AGENTS_LOG_202611.md#L66-L67] |
| 11-20 17:1x | 42e5 | 62.2 | 油門 100 區延長 0.5 m | [src: raw/records/logs/AGENTS_LOG_202611.md#L334] |
| 11-20 17:3x | 5726 | 61.8 | 快照 20261120c 原設定重複 | [src: raw/records/logs/AGENTS_LOG_202611.md#L343] |
| 11-20 18:0x | 93ad | 61.0 | 提速第一步 | [src: raw/records/logs/AGENTS_LOG_202611.md#L383] |
| 11-21 13:3x | b8f5 | 60.4 | 下坡口上限 30 | [src: raw/records/logs/AGENTS.md#L290] |
| 11-21 14:01 | 4a78 | 59.8 | 上段提速 | [src: raw/records/logs/AGENTS.md#L288] |
| 11-21 19:4x | b93e | 59.2 | 換電池後 | [src: raw/records/logs/AGENTS_LOG_202611.md#L779] |
| 11-22 16:25 | ccf1 | 58.2 | 5 整圈無失敗 | [src: raw/records/logs/AGENTS_LOG_202611.md#L1183] |
| 11-23 10:1x | 9b6b | 57.4 | 提速第一組 | [src: raw/records/logs/AGENTS_LOG_202611.md#L1439] |
| 11-23 10:0x | 5b69 | 56.5～57.4 | 提速第二組；效能比約 83%（紀錄） | [src: raw/records/logs/AGENTS_LOG_202611.md#L1452] |
| 11-23 13:4x | 2c42 | 56.4～56.5 | 提速第二階，4 圈最一致 | [src: raw/records/logs/AGENTS_LOG_202611.md#L1538] |
| 11-23 14:3x | d380 | 55.7 | 兩級制直線、彎 2／彎 3 提速 | [src: raw/records/logs/AGENTS_LOG_202611.md#L1584] |
| 11-23 14:5x | 9729 | 55.4 | **舊舵機時期最快**；6 圈無失敗 | [src: raw/records/logs/AGENTS_LOG_202611.md#L1603] |
| 11-23 17:3x | 5f69 | 56.0 | 新舵機時期最快；快照 20261123c | [src: raw/records/logs/AGENTS_LOG_202611.md#L1703] |
| 11-23 18:1x | b541 | 56.5／56.8 | **最終定版**（快照 20261123d） | [src: raw/records/logs/AGENTS_LOG_202611.md#L1730] |

### 期間有紀錄的主要改變

只列紀錄中寫明「上車」或「現役」的改變；後一輪變快不代表就是這項造成，除非紀錄本身寫了對照。

- **11-07～11-08 轉向速率**：慢速轉向版是「舊韌體轉向約 1000 µs/s 時期」，之後的工作台參數為 steer_rate 1500 [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L14] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L17]。
- **11-07 陀螺儀內迴圈**：yaw-inner-r1 依使用者 11-07 的分析加入，用來壓直線 S 型擺動 [src: raw/project/snapshot-20261123d/yaw_inner.py#L1-L6]；細節見 [[experiments/s-weave]]。
- **11-12 間隙補償 ±55**：使用者授權開啟 play_comp ±55／門檻 30 [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L366]。
- **11-13 中心 1480 成為新基準** [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L388]。
- **11-14 lap_pos（以陀螺儀與里程認地標的定位）首次實車**，4 圈 52/52 個地標全找到 [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L434]。
- **11-17 約 30 張/s、間隙補償門檻 30→15**；7afb 主直線擺動明顯變小（只一輪）[src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L642] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L607] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L609]。
- **11-18 內迴圈增益 k 6→4**：對照同日 7a70，彎 4 7.80→7.18 s、主直線 9.65→9.28 s，但斜線變慢 11.14→11.85 s [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L652] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L660]。
- **11-19 韌體油門上限常數 100（pwm100_v1）與主直線油門 100**；落地 100% 實測約 1.44 m/s [src: raw/records/logs/AGENTS.md#L119] [src: raw/records/logs/AGENTS.md#L127]。
- **11-20 各段提速**：油門 100 區延長 0.5 m「主直線、斜線各快約 0.1～0.2 s」；提速第一步左彎 0.92→0.96、上層直線 0.77→0.82 m/s [src: raw/records/logs/AGENTS.md#L305] [src: raw/records/logs/AGENTS.md#L297]。
- **11-21 上段提速**：下坡口上限 30 時「上層直線與下坡合計每圈快約 0.8～0.9 s」[src: raw/records/logs/AGENTS.md#L290]；電池電量明顯影響圈速（推測）[src: raw/records/logs/AGENTS_LOG_202611.md#L779]。
- **11-22 帶狀控制全權**：使用者要求根本解法，彎內舵量改由跑道形狀前饋主導（「帶狀全權」）[src: raw/records/logs/AGENTS.md#L390] [src: raw/records/logs/AGENTS_LOG_202611.md#L1209]。
- **11-23 提速階梯與直線兩級制**：提速第一組使每圈「快約 1 s」（對同算法 baf7／e69d）；兩級制使斜線油門 C1e+1～7 m 全程 100、斜線 8.55～8.81 s（原 8.75～9.15）[src: raw/records/logs/AGENTS_LOG_202611.md#L1439] [src: raw/records/logs/AGENTS_LOG_202611.md#L1573]。
- **11-23 16:34 更換舵機**：之後中心 1475→1445、間隙補償 ±55→±25→±15 [src: raw/records/logs/AGENTS_LOG_202611.md#L1650-L1655] [src: raw/records/logs/AGENTS_LOG_202611.md#L1695]。

### 重大事件

- **11-11 19:40 零件被踢到**：之後的紀錄（含 6430 的 85.8 s）一律視為相機姿態不可靠 [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L17]。
- **11-18 08:3x 輪子摔壞**，當日測試中止 [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L653]。
- **11-20 隊友調左前輪**：直行點先跑到約 1620 再調回約 1470，共用中心改 1470 [src: raw/records/logs/AGENTS.md#L322]。
- **11-21 IMU 俯仰讀數偏移**：自 run-9c6c 起平地相對俯仰 −1.0→−2.2，平地判定常不成立→彎道地圖晚啟動／認錯彎；使用者重新加固並校準 [src: raw/records/logs/AGENTS.md#L282] [src: raw/records/logs/AGENTS.md#L281]。
- **11-21 兩次撞隧道**：run-d137／e6fe 在彎 1 出彎後 C1e+2.6～3.0 m 撞隧道右側 [src: raw/records/logs/AGENTS.md#L284]。
- **11-21 連桿撞斷**：run-4929 第 2 圈彎 1 失控撞隧道，前輪連桿撞斷 [src: raw/records/logs/AGENTS.md#L276]。
- **11-21 18:1x IMU 凍結**：加速度全 0、陀螺儀固定但時間戳照更新，服務仍顯示運行，run-25ca 整輪異常 [src: raw/records/logs/AGENTS.md#L255]。
- **11-22 下坡失敗兩次**：run-46c9 下坡口單格誤差跳動使車在坡口右轉；run-54cb 落地判定在坡頂誤判成已落地 [src: raw/records/logs/AGENTS.md#L224] [src: raw/records/logs/AGENTS.md#L184]。
- **11-23 13:4x 暫停後搬車**：位置在下個地標恢復，但彎 1 帶狀的距離觸發窗失準、彎 2 直線基準航向取歪約 15°，終致 lost(HEADING)；操作規則改為暫停後不搬車 [src: raw/records/logs/AGENTS.md#L164] [src: raw/records/logs/AGENTS_LOG_202611.md#L1541-L1545]。
- **11-23 15:04 舵機故障撞隧道**：run-4abf 第 1 圈 C1e+2.5 m 起車往右加速旋轉到 −112 dps，而指令往左；使用者確認為舵機損壞，16:34 換新舵機並暫把油門上限降到 50 [src: raw/records/logs/AGENTS_LOG_202611.md#L1625-L1626] [src: raw/records/logs/AGENTS_LOG_202611.md#L1632-L1633]。

## 公式與參數

無。

## 未確認

- 計時定義在各時期不同（「彎 1 入→彎 1 入」「彎 1 計圈」「各段加總」），表中數字不能嚴格逐點比較 [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L367] [src: raw/records/logs/AGENTS_LOG_202611.md#L1452]。
- 11-07～11-11 的原始逐格紀錄已刪，只剩文字結論，無法重算 [src: raw/records/logs/AGENTS.md#L375]。
- run 編號只取 4 碼，有重號：11-12 的 a674 完整一圈 83.8 s 與 11-19 的 a674 彎 1 計圈 64.8 s 是不同輪 [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L372] [src: raw/records/logs/AGENTS.md#L326]。
- 11-07 之前（10 月）是否有完整圈紀錄未查；本頁起點取 07 正式操作保存的最早方案 [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L11-L14]。

## 相關條目

- [[experiments/final-performance]]
- [[experiments/s-weave]]
- [[experiments/failures-abandoned]]
- [[control/yaw-inner]]
- [[control/play-comp]]
- [[control/lap-position]]
- [[control/curve-band-ff]]
- [[control/speed-control]]
- [[hardware/steering-servo]]
- [[hardware/imu-mpu6050]]
